import base64
import json
from dataclasses import dataclass, asdict
from pathlib import Path

from coverage.annotate import os


CREDENTIALS_FILE = 'credentials.json'
SYSTEM_PROMPT_FILE = 'system.prompt'
USER_PROMPT_FILE = 'user.prompt'


@dataclass
class Prompts:

    system: str
    user: str

    @classmethod
    def load(cls):
        fp = os.path.abspath(SYSTEM_PROMPT_FILE)
        assert os.path.isfile(fp), f'{fp} does not exist'
        with open(fp, "r") as f:
            system = f.read()

        fp = os.path.abspath(USER_PROMPT_FILE)
        assert os.path.isfile(fp), f'{fp} does not exist'
        with open(fp, "r") as f:
            user = f.read()

        assert system and user, 'invalid prompts'
        print(f"Loaded ChatGPT prompts from files {SYSTEM_PROMPT_FILE}  {USER_PROMPT_FILE}")
        return cls(
            # ensure formatting
            system.replace('\n', ' ').replace('\t', ' ').replace('  ', ' ').replace('   ', ' '),
            user.replace('\n', ' ').replace('\t', ' ').replace('  ', ' ').replace('   ', ' ')
        )


@dataclass
class Credentials:
    google: str
    openai: str

    @classmethod
    def load(cls):
        fp = os.path.abspath(CREDENTIALS_FILE)
        assert os.path.isfile(fp), f'Credentials file {fp} does not exist'
        with open(fp, "r") as f:
            print(f"Using credentials from {CREDENTIALS_FILE}")
            # decode
            keys = json.load(f)
            for k in keys:
                keys[k] = base64.b64decode(keys[k]).decode('utf-8')
            return cls(**keys)


@dataclass
class Address:
    text: str
    lon: float = None
    lat: float = None


@dataclass
class PlaceRef:
    name: str   # establishment or some entity as we know it
    refs: list[Address] = None  # address reference
    raw_gpt: str = None

    def to_file(self, directory: str):
        Path(directory).mkdir(parents=True, exist_ok=True)
        fp = Path(directory) / f'{self.name}.json'
        with open(str(fp), 'w') as f:
            f.write(json.dumps(asdict(self)))