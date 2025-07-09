class ScriptFlow:
    def __init__(self):
        self.blocks = [
            {
                "id": "greeting",
                "text": "Hi, this is Desiree calling on a recorded line from Millennium Information Services. I'm calling regarding your recent insurance request. Is this a good time to talk?",
                "requires_answer": True,
                "next": "verify_identity"
            },
            {
                "id": "verify_identity",
                "text": "Great, I just need to confirm I have the right person. May I know your full name and address please?",
                "requires_answer": True,
                "next": "confirm_inspection"
            },
            {
                "id": "confirm_inspection",
                "text": "Thanks for confirming. This call is part of a home inspection service. Have you recently received any communication about this from your insurance company?",
                "requires_answer": True,
                "next": "dob"
            },
            {
                "id": "dob",
                "text": "Could you please confirm your date of birth?",
                "requires_answer": True,
                "next": "spouse_dob"
            },
            {
                "id": "spouse_dob",
                "text": "And if you're married, may I also have your spouse's date of birth?",
                "requires_answer": False,
                "next": "email"
            },
            {
                "id": "email",
                "text": "Thank you. Could I also get your email address for sending you the confirmation details?",
                "requires_answer": True,
                "next": "policy_type"
            },
            {
                "id": "policy_type",
                "text": "What type of insurance policy do you currently have? For example, homeowners or renters?",
                "requires_answer": True,
                "next": "coverage"
            },
            {
                "id": "coverage",
                "text": "Do you know the coverage amount of your current policy?",
                "requires_answer": False,
                "next": "vehicles"
            },
            {
                "id": "vehicles",
                "text": "Are there any vehicles parked at your home that you’d like us to note during the inspection?",
                "requires_answer": False,
                "next": "appointment"
            },
            {
                "id": "appointment",
                "text": "We’ll need to schedule a brief home inspection. Would Monday at 10 AM or Tuesday at 2 PM work for you?",
                "requires_answer": True,
                "next": "notes"
            },
            {
                "id": "notes",
                "text": "Are there any notes you'd like to add for the inspector? For example, gate code or parking instructions?",
                "requires_answer": False,
                "next": "wrap_up"
            },
            {
                "id": "wrap_up",
                "text": "Thanks so much for your time today. You’ll receive a confirmation email shortly. Have a great day!",
                "requires_answer": False,
                "next": None
            }
        ]

    def get_block(self, block_id):
        for block in self.blocks:
            if block["id"] == block_id:
                return block
        return None
