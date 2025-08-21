import os, base64, logging, time, csv
from mistralai import Mistral

class BatchPdfConv:
    """
    Class for batch processing PDF files with the Mistral OCR API
    and converting them to Markdown files.
    """

    def __init__(self, api_key: str, doc_dir="input", output_dir="output"):
        self.client = Mistral(api_key=api_key)
        self.doc_dir = doc_dir
        self.output_dir = output_dir

        # Configuration
        self.db_csv = f"{output_dir}/processed/processed_files.csv"
        self.log_file = f"{output_dir}/logs/conversion.log"
        self.max_retries = 5
        self.initial_backoff = 1  # en secondes
        self.fieldnames = ['filename', 'status', 'attempts', 'error']

        # Initialize the logging
        self._setup_logging()

    def _setup_logging(self):
        """Configure the logging system."""
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s',
        )
        self.logger = logging.getLogger(__name__)

    def load_processed(self):
        """
        Loads processed file records from a CSV.
        """
        processed = {}
        if os.path.exists(self.db_csv):
            with open(self.db_csv, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    processed[row['filename']] = row
        return processed

    def append_to_db(self, record):
        """
        Adds a treatment record to the CSV database.
        """
        file_exists = os.path.exists(self.db_csv)
        with open(self.db_csv, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(record)

    def get_pdf_files(self):
        """
        Lists all PDF files in the DOC_DIR directory.
        """
        if not os.path.isdir(self.doc_dir):
            self.logger.error(f"Répertoire '{self.doc_dir}' non trouvé.")
            raise FileNotFoundError(f"Répertoire '{self.doc_dir}' non trouvé.")
        return [f for f in os.listdir(self.doc_dir) if f.lower().endswith('.pdf')]

    def encode_pdf(self, pdf_path):
        """
        Encodes the PDF file into a base64 string.
        """
        try:
            with open(pdf_path, "rb") as pdf_file:
                return base64.b64encode(pdf_file.read()).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Échec de l'encodage de {pdf_path}: {e}")
            return None

    def convert_pdf_to_markdown(self, pdf_filename):
        """
        Performs OCR on the PDF and returns the markdown content.
        """
        full_path = os.path.join(self.doc_dir, pdf_filename)
        b64 = self.encode_pdf(full_path)
        if not b64:
            raise RuntimeError("Échec de l'encodage du PDF.")

        # Appel à l'API Mistral OCR
        response = self.client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{b64}"
            },
            include_image_base64=False
        )

        # Construction du contenu markdown
        markdown_content = ""
        for page in response.pages:
            markdown_content += f"## Page {page.index + 1}\n\n"
            markdown_content += page.markdown + "\n\n"

        return markdown_content

    def save_markdown(self, pdf_filename, markdown_text):
        """
        Saves the markdown content to a file.
        """
        base_name = os.path.splitext(pdf_filename)[0]
        output_path = f"{self.output_dir}/markdown/{base_name}.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
        return output_path

    def process_file(self, pdf_filename):
        """
        Processes an individual PDF file with error and retry handling.
        """
        attempts = 0
        backoff = self.initial_backoff

        while attempts < self.max_retries:
            attempts += 1
            try:
                markdown_content = self.convert_pdf_to_markdown(pdf_filename)
                self.save_markdown(pdf_filename, markdown_content)
                self.append_to_db({
                    'filename': pdf_filename, 
                    'status': 'success', 
                    'attempts': attempts, 
                    'error': ''
                })
                return True, ""

            except Exception as e:
                error_msg = str(e)
                self.append_to_db({
                    'filename': pdf_filename, 
                    'status': 'error', 
                    'attempts': attempts, 
                    'error': error_msg
                })
                self.logger.error(f"{pdf_filename} tentative {attempts} échouée: {error_msg}")

                if attempts < self.max_retries:
                    time.sleep(backoff)
                    backoff *= 2

        return False, error_msg

    def process_batch(self, progress_callback=None):
        """
        Processes all PDF files in the directory.
        """
        processed = self.load_processed()
        all_files = self.get_pdf_files()
        total = len(all_files)
        succeeded = sum(1 for r in processed.values() if r['status'] == 'success')
        to_do = [f for f in all_files if processed.get(f, {}).get('status') != 'success']

        stats = {
            'total_files': total,
            'already_converted': succeeded,
            'remaining': len(to_do),
            'converted_count': 0,
            'failed_count': 0,
            'failed_files': []
        }

        for idx, pdf in enumerate(to_do, start=1):
            if progress_callback:
                progress_callback(idx, len(to_do), pdf)

            success, error_msg = self.process_file(pdf)

            if success:
                stats['converted_count'] += 1
            else:
                stats['failed_count'] += 1
                stats['failed_files'].append({'filename': pdf, 'error': error_msg})

            # Pause entre les fichiers pour éviter de surcharger l'API
            if idx < len(to_do):
                time.sleep(3)

        return stats



