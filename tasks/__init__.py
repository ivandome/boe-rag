from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Shared HTTP session with retries
session = Session()
retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)
