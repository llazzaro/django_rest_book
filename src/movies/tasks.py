from celery import shared_task

from movies.services import FileProcessor


@shared_task
def process_file(filename: str, file_type: str) -> int:
    processor = FileProcessor()
    return processor.process(filename, file_type)
