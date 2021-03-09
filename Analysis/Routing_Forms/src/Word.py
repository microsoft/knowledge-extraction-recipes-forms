class Word:
    """Generic representation of a word found by OCR

    The text content of the word is stored in the field "text"

    For the bounding box, we will use the pixel value of the left, right,
    top and bottom indices to represent the position, where the (top, left)
    corner is denoted as (0,0).
    """
    def __init__(
            self,
            text: str,
            left: int,
            right: int,
            top: int,
            bottom: int
        ):
        self.text = text
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom