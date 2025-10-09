# How to Create Your Own Tool Like This

**You don't need to be a programmer. You just need to describe what you want.**

This document shows you how the Style Blender tool was created with minimal input, so you can create your own tools the same way.

## What the Creator Did

The person who "created" this tool didn't write a single line of code. Here's what they actually did:

### Step 1: Identified a Problem

They wanted to use blog_writer but had a real blocker:
- Blog writer needs writing samples to extract your style
- They didn't have existing blog posts
- Their current writing was too dry (technical/business docs)
- Couldn't use someone else's writing directly

### Step 2: Described What They Wanted

They started a conversation with Claude Code and described their idea:

> _Take a look at @scenarios/blog_writer/ especially what it needs for prior examples for writing style to use._
>
> _I'm interested in generating articles using this but I do not have an existing blog and most of my writing is either technical or business oriented so pretty dry._
>
> _I don't think I should just give it someone else's writing as input for style, but I'm wondering if we could make a tool to generate some writing from provided examples from others that I like, then blend that into some new content to use as style input here._
>
> _We would want to create this as another tool under scenarios in the same form as the other examples there. We would want to support taking in txt, md, or pdf writing examples to generate the blended output from to use as a style source for the blog writing tool._

That's it. **No code. No architecture diagrams. No technical specifications.**

### Step 3: Described the Thinking Process

The thinking process that emerged:

1. **Analyze** - "Extract style from each writer separately"
2. **Blend** - "Intelligently combine the styles, not just average them"
3. **Generate** - "Create sample writings that demonstrate the blend"
4. **Make Compatible** - "Output should work directly with blog_writer"

This is the **metacognitive recipe** - the "how should this tool think about the problem?"

### Step 4: Let Claude Code Build It

Claude Code:
- Designed the 3-stage pipeline architecture
- Implemented all the modules (style analyzer, blender, generator)
- Added file discovery and input handling
- Created state management for resume support
- Built the CLI interface with Click
- Handled error recovery and validation

**The creator didn't need to know:**
- How to use Claude Code SDK for AI queries
- How to implement async/await in Python
- How to parse JSON responses reliably
- How to handle recursive file discovery
- Which libraries to use
- How to structure modular code

### Step 5: Iterated Through Real Use

The tool evolved through actual testing. Here are the real issues that came up:

**"Invalid response format - AI not returning JSON"**
- Problem: Blending stage failed with unclear errors
- Root cause: Prompt didn't explicitly say "Return ONLY a JSON object"
- Solution: Fixed prompt to match working Stage 1 pattern

**"Tool says API key missing but I have it in .env"**
- Problem: Environment variables not loaded
- Solution: Added `load_dotenv()` to read `.env` file

**"I have files in different folders, can't organize by directory"**
- Problem: Only supported directories, not individual files
- Solution: Made it flexible - file OR directory = one writer

**"Images folders treated as writers, confusing output"**
- Problem: Discovery included empty directories
- Solution: Only include dirs/subdirs that contain `.md` or `.txt` files

**"Paths like ~/books/file.txt don't work"**
- Problem: Tilde not expanded in Makefile
- Solution: Added shell expansion before passing paths

**"Can't tell why Alice dominates the blend"**
- Problem: No visibility into what was extracted or how blending worked
- Solution: Save all diagnostics - individual profiles, blended profile, all prompts

**"Output mixed with diagnostic files, unclear what to give blog_writer"**
- Problem: Everything in one directory
- Solution: Move samples to clean `output/` subdirectory, create `index.md`

Total time from idea to working tool: One conversation session.

## How You Can Create Your Own Tool

### 1. Find a Real Need

Ask yourself:
- What repetitive task takes too much time?
- What process do I wish was automated?
- What would make my work significantly easier?

**This tool solved:** "I want to use blog_writer but don't have suitable writing samples"

### 2. Describe the Thinking Process

Not the code, the **thinking**. How should the tool approach the problem?

**For style_blender, the thinking was:**
- First analyze each writer separately to understand their style
- Then blend the styles together intelligently
- Then generate new samples that demonstrate the blend
- Make sure it works as input to blog_writer

**Good examples:**
- "First understand X, then do Y based on what you learned, then check if Z is correct"
- "Read these files, find patterns, create a summary, ask me to verify"
- "Take this input, transform it this way, validate it meets these criteria"

**Bad examples:**
- "Use this library to do X" (too technical - let Claude Code choose)
- "Create a function that does Y" (too implementation-focused)
- "Make it work" (too vague - describe HOW it should work)

### 3. Start the Conversation

Use `/ultrathink-task` to describe your goal:

```
/ultrathink-task I want a tool that blends writing styles from multiple authors
to create synthetic samples for blog_writer. It should analyze each writer's style,
intelligently blend them together, and generate new sample writings in the blended
style that I can use as input to blog_writer.
```

### 4. Provide Feedback as Needed

As you test, you'll find issues. Just describe them in natural language:

- "The prompt isn't working - AI responding in prose instead of JSON"
- "I can't tell why one writer is dominating - need diagnostics"
- "The output is confusing - unclear what to use with blog_writer"
- "My paths with ~ aren't working"

Claude Code will fix each issue. Don't worry about getting it perfect upfront.

### 5. Share It Back (Optional)

If your tool works well and others might benefit:
1. Document what it does (README)
2. Document how you created it (this file)
3. Contribute it to scenarios/

## Key Insights from This Creation

### What Worked Well

**Clear Problem Statement**
Explained the actual blocker: "I want to use blog_writer but don't have writing samples, and I can't use someone else's work."

**Referenced Existing Patterns**
Pointing to blog_writer helped Claude Code understand the context and target format.

**Embraced Iteration**
Didn't try to specify everything upfront. Tested, found issues, described problems, got fixes.

**Focused on User Experience**
Each iteration focused on making it easier to use and understand, not on technical perfection.

### What Required Multiple Iterations

**Prompt Engineering**
Getting the AI to return JSON reliably required matching proven patterns from working stages.

**Diagnostics**
Needed multiple rounds to realize what diagnostic data would actually be helpful.

**Input Flexibility**
Started with directories only, evolved to support files after real-world use revealed the need.

**Output Organization**
Took feedback to separate clean outputs from diagnostic files.

## Patterns You Can Reuse

### The Multi-Stage Analysis Pattern

Many tools fit this pattern:
1. **Analyze individual items** (writers, documents, code modules)
2. **Synthesize insights** (blend, summarize, find patterns)
3. **Generate output** (samples, reports, recommendations)

### Comprehensive Diagnostics

Save everything that helps debug:
- Input analysis results
- Prompts used at each stage
- Intermediate synthesis products
- Final outputs

Use this to understand and improve results.

### Clean Output Organization

- User-facing outputs in clean subdirectory
- Diagnostic/debug files in session root
- Index file linking everything together

### Fail-Fast Validation

Check prerequisites upfront:
- API keys at startup
- Minimum input requirements
- File/directory existence

## Common Questions

**Q: Do I need to be a programmer?**
A: No. You need to understand your problem and describe how to think through solving it. Claude Code handles all implementation.

**Q: How long does it take?**
A: Style blender took one conversation session (a few hours including user testing and iteration). Complexity varies by tool.

**Q: What if I don't know the technical details?**
A: Perfect! Describe the problem and desired thinking process. Claude Code makes technical decisions.

**Q: What if my first description isn't perfect?**
A: That's expected and fine. Test it, see what's wrong, describe the issues. Iteration is faster than perfect upfront specs.

**Q: Can I modify the code after it's created?**
A: You can, but it's usually easier to describe what you want changed. These tools follow "describe and regenerate" not "edit line by line."

## Next Steps

- **Try style_blender** to see what's possible
- **Brainstorm ideas** for tools you need
- **Start a conversation** with Claude Code using `/ultrathink-task`
- **Test and iterate** - don't try to specify everything upfront
- **Share what you create** so others can learn

---

**Remember**: The person who created this tool didn't write any code. They described a problem, a thinking process, and provided feedback when testing revealed issues. You can do the same.

For more examples and guidance, see the [main scenarios README](../README.md).
