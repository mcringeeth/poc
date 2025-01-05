import json
import logging
import os
import sys
import traceback
import zipfile
from typing import Dict, Any

from my_proof.proof import Proof

INPUT_DIR, OUTPUT_DIR, SEALED_DIR = '/input', '/output', '/sealed'

logging.basicConfig(level=logging.INFO, format='%(message)s')


def load_config() -> Dict[str, Any]:
    """Load proof configuration from environment variables."""
    config = {
        'dlp_id': 8,  # Set your own DLP ID here
        'use_sealing': os.path.isdir(SEALED_DIR),
        'input_dir': INPUT_DIR,
        'telegram_bot_access_key': os.environ.get('TELEGRAM_BOT_ACCESS_KEY', None),
        'tg_init_data': os.environ.get('TELEGRAM_INIT_DATA', None).strip('"\'') if os.environ.get('TELEGRAM_INIT_DATA') else None,
        'filebase_access_key_id': os.environ.get('FILEBASE_ACCESS_KEY_ID', None),
        'filebase_secret_access_key': os.environ.get('FILEBASE_SECRET_ACCESS_KEY', None),
    }
    return config


def run() -> None:
    """Generate proofs for all input files."""
    config = load_config()
    input_files_exist = os.path.isdir(INPUT_DIR) and bool(os.listdir(INPUT_DIR))

    if not input_files_exist:
        raise FileNotFoundError(f"No input files found in {INPUT_DIR}")
    extract_input()

    proof = Proof(config)
    proof_response = proof.generate()

    output_path = os.path.join(OUTPUT_DIR, "results.json")
    with open(output_path, 'w') as f:
        json.dump(proof_response.model_dump(), f, indent=2)
    logging.info(f"Proof generation complete: {proof_response}")


def extract_input() -> None:
    """
    If the input directory contains any zip files, extract them and remove the original zip files
    """
    logging.info(f"Scanning {INPUT_DIR} for zip files...")
    zip_files_found = False
    
    for input_filename in os.listdir(INPUT_DIR):
        input_file = os.path.join(INPUT_DIR, input_filename)

        if zipfile.is_zipfile(input_file):
            zip_files_found = True
            logging.info(f"Found zip file: {input_filename}")
            try:
                with zipfile.ZipFile(input_file, 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                    logging.info(f"Zip contains: {', '.join(file_list)}")
                    logging.info(f"Extracting contents of {input_filename}...")
                    zip_ref.extractall(INPUT_DIR)
                os.remove(input_file)
                logging.info(f"Successfully extracted and removed: {input_filename}")
            except Exception as e:
                logging.error(f"Error processing zip file {input_filename}: {str(e)}")
                raise
    
    if not zip_files_found:
        logging.info("No zip files found in input directory")


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(f"Error during proof generation: {e}")
        traceback.print_exc()
        sys.exit(1)
