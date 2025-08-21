# Lessons Learned - Frederik's Development Philosophy

## Clean Fail vs Obscure Fallbacks

**Core Principle**: "Better to clearly state that something doesn't work (and why) than to fall back on unreliable solutions."

### Why This Matters:
- **Debugging**: When something fails cleanly, you immediately know what's wrong
- **Reliability**: Fallbacks often mask real configuration issues
- **Maintainability**: Clean failures force proper setup, fallbacks allow technical debt
- **User Trust**: Clear error messages build confidence, mysterious behaviors don't

### Examples:

**❌ Bad (Obscure Fallback)**:
```python
try:
    from required_module import important_function
except ImportError:
    # Silent fallback to unreliable alternative
    def important_function():
        return "maybe_works_sometimes"
```

**✅ Good (Clean Fail)**:
```python
# Import required module - REQUIRED, no fallbacks
from required_module import important_function
# If this fails, the error message clearly shows what's missing
```

### Frederik's Quote:
> "Als fuzzy category matcher er niet is dan kan je dat gewoon als antwoord geven. Beter zeggen dat het niet werkt (en waarom het niet werkt) dan terug te vallen op onbetrouwbare zaken."

### Application in Code:
- Remove try/except blocks around critical imports
- Let ImportError bubble up with clear messages
- Don't create fallback functions that work "sometimes"
- Force proper configuration instead of masking issues
- Make dependencies explicit and required

This philosophy leads to more robust, maintainable, and debuggable code.
