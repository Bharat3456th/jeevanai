# (State / UT name, best language code that Google Translate supports)
STATES = [
    ("Andhra Pradesh", "te"), ("Arunachal Pradesh", "hi"), ("Assam", "as"), ("Bihar", "hi"),
    ("Chhattisgarh", "hi"), ("Goa", "kok"), ("Gujarat", "gu"), ("Haryana", "hi"),
    ("Himachal Pradesh", "hi"), ("Jharkhand", "hi"), ("Karnataka", "kn"), ("Kerala", "ml"),
    ("Madhya Pradesh", "hi"), ("Maharashtra", "mr"), ("Manipur", "mni-Mtei"), ("Meghalaya", "en"),
    ("Mizoram", "lus"), ("Nagaland", "en"), ("Odisha", "or"), ("Punjab", "pa"), ("Rajasthan", "hi"),
    ("Sikkim", "ne"), ("Tamil Nadu", "ta"), ("Telangana", "te"), ("Tripura", "bn"),
    ("Uttar Pradesh", "hi"), ("Uttarakhand", "hi"), ("West Bengal", "bn"),
    # Union Territories
    ("Andaman and Nicobar Islands", "hi"), ("Chandigarh", "pa"),
    ("Dadra and Nagar Haveli and Daman and Diu", "gu"), ("Delhi", "hi"), ("Jammu and Kashmir", "ur"),
    ("Ladakh", "hi"), ("Lakshadweep", "ml"), ("Puducherry", "ta"),
]
STATE_NAMES = {name for name, _ in STATES}
OCCUPATIONS = ["Student", "Job seeker", "Working professional", "Business owner",
               "Teacher / Educator", "Other"]
