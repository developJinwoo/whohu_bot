import pickle
import os
import random
from datetime import datetime, timedelta
import asyncio
import aiofiles

import config

async def pickler(PATH, _dict):
    async with aiofiles.open( PATH, 'wb' ) as f:
        pickled_foo = pickle.dumps( _dict)
        await f.write(pickled_foo)

async def unpickler(PATH):
    async with aiofiles.open( PATH, "rb" ) as f:
        pickled_foo = await f.read()
        return pickle.loads(pickled_foo)
