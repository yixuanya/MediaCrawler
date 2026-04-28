"""Allow `python -m wenzhi_collectors` to run the collector."""
from wenzhi_collectors.run_collect_once import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
