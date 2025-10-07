"""Basic tests for style blender."""

from pathlib import Path

import pytest

from ..content_generator import ContentGenerator
from ..state import BlendedStyleProfile
from ..state import StyleProfile
from ..style_analyzer import StyleAnalyzer
from ..style_blender import StyleBlender


@pytest.fixture
def sample_writers_dir():
    """Return path to sample writers directory."""
    return Path(__file__).parent / "sample_writers"


@pytest.fixture
def technical_profile():
    """Create a technical writer profile."""
    return StyleProfile(
        writer_name="writer_a",
        tone="technical",
        vocabulary_level="advanced",
        sentence_structure="complex and precise",
        paragraph_length="medium",
        common_phrases=["Let's consider", "The solution involves", "This approach"],
        writing_patterns=["States facts clearly", "Uses technical terms", "Explains systematically"],
        voice="mostly passive",
        examples=["The process begins with analysis.", "Performance optimization requires consideration."],
        sample_count=2,
    )


@pytest.fixture
def conversational_profile():
    """Create a conversational writer profile."""
    return StyleProfile(
        writer_name="writer_b",
        tone="conversational",
        vocabulary_level="simple",
        sentence_structure="varied and flowing",
        paragraph_length="short",
        common_phrases=["Here's the thing", "You know what", "Let's talk about"],
        writing_patterns=["Uses questions", "Personal anecdotes", "Direct address to reader"],
        voice="mostly active",
        examples=["Let me tell you what worked for me.", "You won't believe what happened!"],
        sample_count=2,
    )


class TestStyleAnalyzer:
    """Test style analyzer functionality."""

    @pytest.mark.asyncio
    async def test_extract_style_basic(self, sample_writers_dir):
        """Test basic style extraction."""
        analyzer = StyleAnalyzer()
        writer_a_dir = sample_writers_dir / "writer_a"

        if writer_a_dir.exists():
            profile = await analyzer.extract_style(writer_a_dir)

            assert profile is not None
            assert profile.writer_name == "writer_a"
            assert profile.tone  # Should have a tone
            assert profile.vocabulary_level  # Should have vocabulary level

    @pytest.mark.asyncio
    async def test_handle_missing_directory(self):
        """Test handling of missing directory."""
        analyzer = StyleAnalyzer()
        profile = await analyzer.extract_style(Path("/nonexistent/path"))

        assert profile is not None  # Should return default profile
        assert profile.writer_name == "unknown"


class TestStyleBlender:
    """Test style blending functionality."""

    @pytest.mark.asyncio
    async def test_blend_two_styles(self, technical_profile, conversational_profile):
        """Test blending two different styles."""
        blender = StyleBlender()
        profiles = [technical_profile, conversational_profile]

        blended = await blender.blend_styles(profiles)

        assert blended is not None
        assert len(blended.source_writers) == 2
        assert "writer_a" in blended.source_writers
        assert "writer_b" in blended.source_writers
        assert blended.blending_strategy  # Should have a strategy

    @pytest.mark.asyncio
    async def test_reject_single_profile(self, technical_profile):
        """Test that blending requires at least 2 profiles."""
        blender = StyleBlender()

        with pytest.raises(ValueError, match="at least 2 profiles"):
            await blender.blend_styles([technical_profile])


class TestContentGenerator:
    """Test content generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_sample(self, technical_profile, conversational_profile):
        """Test generating a sample with blended style."""
        # Create a simple blended profile
        blended = BlendedStyleProfile(
            source_writers=["writer_a", "writer_b"],
            tone="balanced technical",
            vocabulary_level="moderate",
            sentence_structure="varied",
            paragraph_length="medium",
            common_phrases=["Let's explore", "Here's how"],
            writing_patterns=["Clear explanations", "Engaging examples"],
            voice="mostly active",
            blending_strategy="technical clarity with conversational tone",
        )

        generator = ContentGenerator()
        sample = await generator.generate_sample(blended, sample_number=1)

        assert sample is not None
        assert len(sample) > 100  # Should generate substantial content
        assert sample.startswith("#")  # Should start with markdown title

    def test_fallback_generation(self):
        """Test fallback generation when AI fails."""
        generator = ContentGenerator()
        sample = generator._generate_fallback("technology and innovation", 1)

        assert sample is not None
        assert "Future" in sample or "Digital" in sample
        assert sample.startswith("#")


class TestEndToEnd:
    """Test complete pipeline integration."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, sample_writers_dir, tmp_path):
        """Test the complete style blending pipeline."""
        # Skip if sample writers don't exist
        if not sample_writers_dir.exists():
            pytest.skip("Sample writers directory not found")

        # Analyze writers
        analyzer = StyleAnalyzer()
        profiles = []

        for writer_dir in sample_writers_dir.iterdir():
            if writer_dir.is_dir():
                profile = await analyzer.extract_style(writer_dir)
                profiles.append(profile)

        if len(profiles) < 2:
            pytest.skip("Not enough sample writers for testing")

        # Blend styles
        blender = StyleBlender()
        blended = await blender.blend_styles(profiles)

        assert blended is not None
        assert blended.blending_strategy

        # Generate sample
        generator = ContentGenerator()
        sample = await generator.generate_sample(blended)

        assert sample is not None
        assert len(sample) > 100

        # Save to file
        output_file = tmp_path / "test_output.md"
        output_file.write_text(sample)

        assert output_file.exists()
        assert output_file.stat().st_size > 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
