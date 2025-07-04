from pydantic import BaseModel
from typing import Optional

class ScriptBlock(BaseModel):
    id: str
    text: str
    next_block: Optional[str] = None
    is_question: bool = False
    requires_response: bool = False
    condition: Optional[str] = None

class ScriptFlow:
    def __init__(self):
        self.blocks = {
            "greeting": ScriptBlock(
                id="greeting",
                text="Hello, this is Desiree from Millennium Information Services. May I proceed?",
                next_block="intro",
                is_question=True,
                requires_response=True
            ),
            "intro": ScriptBlock(
                id="intro",
                text="Your insurance needs a 10-minute interview. Is now a good time?",
                next_block="q1",
                is_question=True,
                requires_response=True,
                condition="yes"
            ),
            "q1": ScriptBlock(
                id="q1",
                text="Are there working smoke detectors? Yes all, Yes not all, None, Unknown?",
                next_block="q2",
                is_question=True,
                requires_response=True
            ),
            "q2": ScriptBlock(
                id="q2",
                text="Are there working carbon monoxide detectors? Yes all, Yes not all, None, Unknown?",
                next_block="q3",
                is_question=True,
                requires_response=True
            ),
            "q3": ScriptBlock(
                id="q3",
                text="Are there working fire extinguishers? Yes all, Yes not all, None, Unknown?",
                next_block="q4",
                is_question=True,
                requires_response=True
            ),
            "q4": ScriptBlock(
                id="q4",
                text="Distance to closest fire station in miles?",
                next_block="q5",
                is_question=True,
                requires_response=True
            ),
            "q5": ScriptBlock(
                id="q5",
                text="Nearest fire hydrant: <100 ft, 100–1000 ft, >1000 ft, or none?",
                next_block="q6",
                is_question=True,
                requires_response=True
            ),
            "q6": ScriptBlock(
                id="q6",
                text="Is your home in city limits? Yes or No?",
                next_block="q7",
                is_question=True,
                requires_response=True
            ),
            "q7": ScriptBlock(
                id="q7",
                text="What year was your roof installed, or unknown?",
                next_block="q8",
                is_question=True,
                requires_response=True
            ),
            "q8": ScriptBlock(
                id="q8",
                text="Is your home visible from the main road? Yes or No?",
                next_block="q9",
                is_question=True,
                requires_response=True
            ),
            "q9": ScriptBlock(
                id="q9",
                text="Is your home accessible year-round? Yes or No?",
                next_block="q10",
                is_question=True,
                requires_response=True
            ),
            "q10": ScriptBlock(
                id="q10",
                text="How many homes in eyesight?",
                next_block="q11",
                is_question=True,
                requires_response=True
            ),
            "q11": ScriptBlock(
                id="q11",
                text="Distance in yards from main paved road?",
                next_block="q12",
                is_question=True,
                requires_response=True
            ),
            "q12": ScriptBlock(
                id="q12",
                text="Special construction? No, Log, Manufactured, Mobile, Modular, Frame, Steel, Dome, Earth?",
                next_block="q13",
                is_question=True,
                requires_response=True
            ),
            "q13": ScriptBlock(
                id="q13",
                text="Average ceiling height in feet? Any vaulted?",
                next_block="q14",
                is_question=True,
                requires_response=True
            ),
            "q14": ScriptBlock(
                id="q14",
                text="Heating type? Gas, Oil, or Other?",
                next_block="q15",
                is_question=True,
                requires_response=True
            ),
            "q15": ScriptBlock(
                id="q15",
                text="Schedule a follow-up appointment? Yes or No?",
                next_block="wrapup",
                is_question=True,
                requires_response=True
            ),
            "wrapup": ScriptBlock(
                id="wrapup",
                text="Thank you. Inspector will visit soon. Have a great day!",
                next_block=None
            ),
        }

    def get_block(self, block_id: str) -> ScriptBlock:
        return self.blocks.get(block_id)

    def get_next_block_id(self, block_id: str, response: str = None) -> Optional[str]:
        block = self.blocks.get(block_id)
        if block.condition and response and block.condition.lower() not in response.lower():
            return None
        return block.next_block
    