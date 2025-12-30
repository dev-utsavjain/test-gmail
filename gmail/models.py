from dataclasses import dataclass, field

@dataclass
class ParsedEmail:
    text: str = ""
    html: str = ""
    inline_images: list = field(default_factory=list)
    attachments: list = field(default_factory=list)




