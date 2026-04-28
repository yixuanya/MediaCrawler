"""Allow `python -m wenzhi_pipeline` or `python -m wenzhi_pipeline.run_pipeline_once`."""
import asyncio
from wenzhi_pipeline.run_pipeline_once import main

if __name__ == "__main__":
    asyncio.run(main())
