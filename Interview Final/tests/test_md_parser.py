import pytest
import sys
import os

# Add the project root to the Python path to allow importing 'utils'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from utils.md_parser import MarkdownParser

# Sample Markdown content for testing
SAMPLE_MD = """
# Main Title

This is some introductory text. It includes `inline code` and a [link](http://example.com).

## Section One

Content for section one. *Emphasis* and **bold text**.

```json
{
  "config_one": {
    "key1": "value1",
    "enabled": true
  }
}
```

More text here.

## Section Two

Content for section two.
Here's an image: ![Alt text](/path/to/image.png)

```python
print("This is python code, should be removed in raw text")
```

Another JSON section:

```json
{
  "config_two": {
    "mode": "test",
    "threshold": 0.5
  }
}
```

<!-- HTML Comment -->
<p>HTML Paragraph</p>

Final paragraph.
"""

# --- Test Fixtures ---

@pytest.fixture
def parser():
    """Provides a MarkdownParser instance."""
    return MarkdownParser()

# --- Test Functions ---

def test_extract_raw_text(parser):
    """Test extraction of raw text, removing markdown syntax."""
    expected_raw_text = (
        "# Main Title\n\n"  # Headings are kept currently
        "This is some introductory text. It includes  and a link.\n\n" # inline code removed, link text kept
        "## Section One\n\n" # Headings kept
        "Content for section one. *Emphasis* and **bold text**.\n\n" # Emphasis/bold kept
        "More text here.\n\n" # Text after JSON kept
        "## Section Two\n\n" # Headings kept
        "Content for section two.\nHere's an image: \n\n" # Image removed
        "Another JSON section:\n\n" # Text before JSON kept
        "HTML Paragraph\n\n"  # Added "HTML Paragraph" here
        "Final paragraph."
    ).strip()
    
    actual_raw_text = parser.extract_raw_text(SAMPLE_MD)
    # Basic whitespace normalization for comparison flexibility
    assert ' '.join(actual_raw_text.split()) == ' '.join(expected_raw_text.split())

def test_extract_json_sections(parser):
    """Test extraction of JSON sections."""
    expected_json = {
        "config_one": {
            "key1": "value1",
            "enabled": True
        },
        "config_two": {
            "mode": "test",
            "threshold": 0.5
        }
    }
    actual_json = parser.extract_json_sections(SAMPLE_MD)
    assert actual_json == expected_json

def test_extract_specific_section(parser):
    """Test extraction of a specific named section."""
    expected_section_one_content = (
        "Content for section one. *Emphasis* and **bold text**.\n\n"
        "```json\n{\n  \"config_one\": {\n    \"key1\": \"value1\",\n    \"enabled\": true\n  }\n}\n```\n\n"
        "More text here."
    ).strip()
    
    actual_section_one = parser.extract_section(SAMPLE_MD, "Section One")
    assert actual_section_one is not None
    # Normalize whitespace
    assert ' '.join(actual_section_one.split()) == ' '.join(expected_section_one_content.split())

def test_extract_nonexistent_section(parser):
    """Test extracting a section that doesn't exist."""
    actual_section = parser.extract_section(SAMPLE_MD, "NonExistent Section")
    assert actual_section is None
