from celery import shared_task
import logging

@shared_task
def add_together(x, y, *args, **kwargs):
    logging.info(f"Adding {str(x)} and {str(y)}")
    logging.info(f"args: {str(args)}")
    logging.info(f"kwargs: {str(kwargs)}")
    return x + y