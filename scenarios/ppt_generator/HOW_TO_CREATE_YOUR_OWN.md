# How to Create Your Own Tool Like This

**You don't need to be a programmer. You just need to describe what you want.**

This document shows you how the PPT Generator was created with minimal input, so you can create your own tools the same way.

## What the Creator Did

The person who "created" this tool didn't write most of the code. Here's what they actually did:

### Step 1: Described What They Wanted

They started a conversation with Amplifier and described their goal in natural language:

> *I need a tool that can take markdown content files and turn them into PowerPoint presentations.*
>
> *It should read the content, understand what it's about, then structure it into a logical presentation flow.*
>
> *I want it to generate slide content - titles, bullet points, speaker notes. And I want it to be smart about creating visuals - when does a slide need a diagram? When would an image help? It should generate those too.*
>
> *Before it assembles the final PowerPoint, let me review the layout and content. I should be able to add comments where I want changes, and it should regenerate those specific slides based on my feedback.*
>
> *And make it work with my company's PowerPoint template for branding.*

That's it. **No code. No architecture diagrams. No technical specifications.**

### Step 2: Described the Thinking Process

Notice what they described:
1. "Understand the content deeply"
2. "Structure it into a presentation flow"
3. "Generate detailed slide content"
4. "Plan which visuals would help"
5. "Create diagrams and images"
6. "Let me review and give feedback"
7. "Apply my feedback to specific slides"
8. "Assemble the final PowerPoint"

This is what we call a **metacognitive recipe** - the "how should this tool think about the problem?" They described the thinking process, not the implementation.

### Step 3: Let Amplifier Build It

Amplifier:
- Used specialized agents (zen-architect, modular-builder, bug-hunter)
- Designed the 7-stage pipeline architecture
- Implemented all the code modules
- Added state management for interruption/resume
- Created intelligent visual planning
- Built diagram generation with Mermaid
- Integrated DALL-E for image generation
- Implemented the interactive review system
- Created feedback application with slide regeneration
- Built the PowerPoint assembly with smart layouts
- Handled template integration
- Created the CLI interface

**The creator didn't need to know:**
- How to work with the python-pptx library
- How to implement async/await patterns
- How to manage multi-stage pipeline state
- How to generate Mermaid diagrams
- How to call DALL-E APIs
- How to parse bracketed comments
- How to regenerate specific slides with LLM
- How to position visuals without overlapping
- Which AI models to use for each stage
- How to handle resumability

### Step 4: Iterated to Refine

The tool didn't work perfectly on the first try. Real issues discovered:

**Issue 1: "Diagrams and text are overlapping on slides"**
- **Problem**: Manual positioning caused overlap
- **Solution**: Switched to PowerPoint's placeholder system
- **Result**: Clean layouts, no overlap

**Issue 2: "The review stage shows a preview but my comments weren't applied"**
- **Problem**: Comments were parsed but not used to regenerate slides
- **Solution**: Implemented feedback processor that regenerates affected slides
- **Result**: Comments now drive slide regeneration

**Issue 3: "SlidePlaceholders errors in assembly"**
- **Problem**: Incorrect API usage (`.values()` on non-dict)
- **Solution**: Fixed to iterate correctly over placeholders
- **Result**: Assembly completes without errors

Amplifier fixed these through conversation. Total time from idea to working tool: one extended session with iterations.

## How You Can Create Your Own Tool

### 1. Find a Real Need

Ask yourself:
- What repetitive task takes too much time?
- What process do I wish was automated?
- What would make my work significantly easier?

**Examples from this repo:**
- "Writing blog posts takes hours" → blog-writer
- "Articles need good images" → article-illustrator
- "Creating presentations is tedious" → ppt-generator

### 2. Describe the Thinking Process

Not the code, the **thinking**. How should the tool approach the problem?

**Good examples:**
- "First analyze the content to understand it, then structure it logically, then generate slides, then create visuals, then let me review"
- "Read my writings to learn my style, draft content matching it, check accuracy, check style, get my feedback"
- "Understand the article, find where images help, create relevant prompts, generate images, integrate them"

**Bad examples:**
- "Use python-pptx to create slides" (too technical)
- "Create a class that generates presentations" (too implementation-focused)
- "Make a PowerPoint tool" (too vague)

### 3. Start the Conversation

In your Amplifier environment:

```bash
claude
```

Then describe your goal using `/ultrathink-task`:

```
/ultrathink-task Create me a tool that [describe your goal and thinking process]
```

**Example from PPT Generator creation**:
```
/ultrathink-task Create a tool that takes markdown files and generates PowerPoint presentations.

It should:
1. Understand the content and main topics
2. Structure it into a logical presentation flow
3. Generate slide content with titles, bullets, and speaker notes
4. Determine where visuals would help (diagrams vs images)
5. Generate technical diagrams for concepts
6. Generate AI images for engagement
7. Let me review and add feedback as bracketed comments
8. Regenerate slides based on my feedback
9. Assemble everything into a PowerPoint file

Make it work with custom templates and be resumable.
```

### 4. Provide Feedback as Needed

When you try the tool, you'll find issues or want improvements:
- "Slides are overlapping"
- "My comments aren't being applied"
- "Can we support custom templates?"
- "The review stage hangs - is that normal?"

Just describe what's wrong or what you want added. Amplifier will iterate.

### 5. Share It Back (Optional)

If your tool works well and others might benefit:
1. Document what it does (like this tool's README)
2. Document how you created it (like this file)
3. Contribute it to the scenarios/ directory
4. Help others learn from your creation

## Real Tool Ideas You Could Create

Here are ideas that follow the same pattern:

### Beginner-Friendly

**Meeting Notes Summarizer**
- **What it does**: Turns rambling meeting notes into structured summaries
- **The recipe**: Read notes → Identify decisions/action items → Organize by topic → Format as summary
- **Why it's good**: Clear problem, straightforward thinking process

**Email Composer**
- **What it does**: Drafts professional emails from bullet points
- **The recipe**: Understand context → Match tone to recipient → Draft email → Check clarity
- **Why it's good**: Daily use case, obvious value

### Intermediate

**Technical Spec Generator**
- **What it does**: Analyzes code and generates comprehensive specifications
- **The recipe**: Analyze code → Extract components → Document interfaces → Write usage examples
- **Why it's good**: Saves hours of documentation work

**Presentation Translator**
- **What it does**: Converts presentations between formats (PPT → Google Slides → Keynote)
- **The recipe**: Parse source → Extract structure → Adapt to target format → Assemble
- **Why it's good**: Solves real format compatibility issues

### Advanced

**Multi-Format Content Publisher**
- **What it does**: Takes content and generates blog post, slides, social media posts
- **The recipe**: Understand content → Adapt to each format → Generate assets → Review each output
- **Why it's good**: Maximizes content reuse across channels

## The Key Principles

### 1. You Describe, Amplifier Builds

You don't need to know how to code. You need to know:
- What problem you're solving
- How a human would think through solving it
- What a good solution looks like

### 2. Metacognitive Recipes Are Powerful

A clear thinking process is all you need:
- "First understand X, then create Y, then check Z"
- "Repeat this stage until criteria met"
- "Get feedback and incorporate it"

This guides the entire implementation.

### 3. Iteration Is Normal and Fast

Your first description won't be perfect. That's fine!

The PPT Generator evolved through our conversation:
- Initial creation with basic features
- Fixed placeholder positioning
- Added review stage
- Implemented feedback application
- Fixed various bugs

Each improvement came from describing the problem, not coding the solution.

### 4. Working Tools Beat Perfect Specs

The tools in scenarios/ are experimental but genuinely useful. They solve real problems right now. Improvements come as needs emerge, not from trying to anticipate everything upfront.

## The PPT Generator's Journey

### Initial Request

*"Create a tool that generates PowerPoint presentations from markdown content. It should analyze the content, structure it into slides, generate visuals (diagrams and images), and assemble a professional presentation."*

Result: Basic multi-stage pipeline with content generation

### Refinements (Through Use)

- "Slides are overlapping" → Implemented proper placeholder system
- "I want to review before final assembly" → Added review stage with preview
- "My feedback isn't being applied" → Implemented slide regeneration
- "SlidePlaceholders errors" → Fixed API usage bugs
- "Need to work with corporate templates" → Added template support

All of this happened through conversation, not code editing.

## Getting Started

1. **Complete the [Amplifier setup](../../README.md#-step-by-step-setup)**
2. **Think about your need** - What would make your work easier?
3. **Describe the thinking process** - How should the tool approach it?
4. **Start the conversation** - Use `/ultrathink-task` to describe your goal
5. **Iterate to refine** - Provide feedback as you use it
6. **Share it back** - Help others by contributing your tool

## Common Questions

**Q: Do I need to be a programmer?**
A: No. You need to understand the problem domain and be able to describe a thinking process. Amplifier handles all the implementation.

**Q: How long does it take?**
A: The PPT generator took one extended session with iterations. Simpler tools might take less, more complex ones might need 2-3 sessions.

**Q: What if I don't know how to describe the thinking process?**
A: Start with: "I want a tool that does X. It should first do A, then B, then C." Amplifier will help you refine from there.

**Q: Can I modify the code after Amplifier creates it?**
A: You can, but it's usually easier to describe what you want changed and let Amplifier update it. Remember: these tools follow the "describe and regenerate" pattern, not the "edit line by line" pattern.

**Q: What if my tool idea is too complex?**
A: Break it into phases. Create a simple version first, then add features one at a time. The PPT generator started simpler and grew through use.

**Q: How do I know if my idea is good for a scenario tool?**
A: If it:
- Solves a real problem you face regularly
- Can be described as a thinking process
- Would benefit from AI's analytical and creative capabilities
- Would save significant time if automated

Then it's probably a great candidate!

## Next Steps

- **Try the ppt-generator tool** to see what's possible
- **Study the blog_writer** as another exemplar
- **Brainstorm your own tool ideas** - what would help your work?
- **Start a conversation** with Amplifier using `/ultrathink-task`
- **Share what you create** so others can learn

---

**Remember**: The person who created this tool described what they wanted and how it should think. They didn't write the implementation. You can do the same.

For more examples and guidance, see the [main scenarios README](../README.md) and study the [blog_writer](../blog_writer/) as the definitive exemplar.
