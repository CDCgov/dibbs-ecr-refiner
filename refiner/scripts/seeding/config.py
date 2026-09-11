import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
TES_DATA_DIR = DATA_DIR / "source-tes-groupers"
ENV_PATH = BASE_DIR / ".env"

# filename prefix the fetch pipeline gives the eICR triggering shards it
# writes into TES_DATA_DIR; sharding appends '.partNN', hence prefix rather
# than exact name
TRIGGER_FILE_PREFIX = "eicr_triggering"
