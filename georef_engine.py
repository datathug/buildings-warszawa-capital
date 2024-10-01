import json
import os
import time
from datetime import datetime
from hashlib import md5

from definitions import PlaceRef, Credentials, Prompts, Address

from openai import OpenAI, ChatCompletion


CHATGPT_TEMPERATURE = 0.5   # use smaller values for geocoding - no creativity
OPENAI_MODEL = 'gpt-4o'
TOKENS_COUNT_FILE = "tokens.count"

# placeholder
NO_ADDRESS = 'NO_ADDRESS'


class ChatGptApi(OpenAI):

    prev_messages: list
    last_call_elapsed: float    # seconds
    results: list
    prompts: Prompts

    tokens_file = TOKENS_COUNT_FILE
    token_count: int = 0
    token_count_at_start: int = 0
    session_tokens_in: int = 0
    session_tokens_out: int = 0
    last_call_tokens: int = -1

    last_n_chars_for_key_strorage: int = 6

    def __init__(self):
        super().__init__(api_key=Credentials.load().openai)
        self.prev_messages = []
        self.results = []
        self.load_token_count()
        # self.chat.completions.create = self.count_tokens(self.chat.completions.create)  # wrap
        print(f"{datetime.now().ctime()} OpenAI API client initiated")
        self.prompts = Prompts.load()

    def load_token_count(self):
        if os.path.isfile(self.tokens_file):
            with open(self.tokens_file) as f:
                key_counts = json.load(f)
                self.token_count_at_start = self.token_count = key_counts.get(self.api_key_identifier, 0)
                print(f"Loaded token count of {self.token_count} used before")
        else:
            self.token_count_at_start = self.token_count = 0

    @property
    def md5_key(self) -> str:
        return md5(bytes(self.api_key, 'utf-8')).hexdigest()

    @property
    def api_key_identifier(self):
        return "....{} ( MD5 {})".format(self.api_key[-self.last_n_chars_for_key_strorage:], self.md5_key)

    def record_tokens(self):
        if self.token_count and self.token_count != self.token_count_at_start:

            # create file if does not exist
            if not os.path.isfile(self.tokens_file):
                with open(self.tokens_file, 'w') as f:
                    f.write('{ }')  # write empty JSON to avoid JSONDecode error - only when empty or new file
                prev_state = {}

            else:
                with open(self.tokens_file, 'r') as f:
                    prev_state = json.load(f)

            prev_state[self.api_key_identifier] = self.token_count     # set updated value after request performed
            with open(self.tokens_file, 'w') as f:
                json.dump(prev_state, f)

    @staticmethod
    def parse_gpt_response(msg: str) -> list[str]:

        processed = [
            x.strip().split('.', 1)[-1].strip() for x in msg.split('\n')
        ]
        return [i for i in filter(
                lambda x: len(x) > 0,
                processed
            )
        ]

    def perform_completion(self, *args, **kwargs):

        b = time.perf_counter()
        raw_comp = self.chat.completions.with_raw_response.create(*args, **kwargs)
        self.last_call_elapsed = time.perf_counter() - b

        comp: ChatCompletion = raw_comp.parse()
        headers = raw_comp.headers
        self.results.append(comp)

        # TODO use headers info to keep track of tokens

        try:
            self.session_tokens_in += comp.usage.prompt_tokens
            self.session_tokens_out += comp.usage.completion_tokens
            self.token_count += comp.usage.total_tokens
            self.last_call_tokens = comp.usage.total_tokens
            self.record_tokens()
        finally:
            return comp

    def geocoding_prompt(self, place: PlaceRef = None):

        assert place, 'must be a valid place'

        completion = self.perform_completion(
            messages=[
                {
                    'role': 'system',
                    'content': self.prompts.system.format(no_address=NO_ADDRESS),
                },
                {
                    "role": "user",
                    "content": self.prompts.user.format(institution_name=place.name),
                }
            ],
            model=OPENAI_MODEL,
            temperature=CHATGPT_TEMPERATURE
        )
        gpt_messages: list[str] = [x.message.content for x in completion.choices]

        # set and parse in place
        place.raw_gpt = gpt_messages[0]
        if NO_ADDRESS in place.raw_gpt:
            print(f'WARN: returned no address flag for {place.name}')
            print('RAW RESPONSE: ', place.raw_gpt)
            pass
        place.refs = [Address(text=x) for x in self.parse_gpt_response(place.raw_gpt)]

        log_msg = '{} s ({}): {} / {} | {}'.format(
            int(self.last_call_elapsed),
            len(completion.choices),    # number of choices returned
            self.last_call_tokens,
            self.token_count,
            ' + '.join([x.text for x in place.refs])
        )
        print(log_msg)

        return place

