# Revit MCP Tool Usage Guide

## 🚨 CRITICAL - READ THIS BEFORE ANY COMMAND EXECUTION

**ALWAYS read this document before executing commands or writing any files.**

This guide defines which tools to use for each task and establishes the patterns and safety measures for the Revit MCP project based on lessons learned from character encoding issues and international project requirements.

## 💬 RESPONSE STYLE GUIDELINES

### Keep Responses Short & Actionable
- ✅ **Give direct, concise answers**
- ✅ **Suggest specific follow-up options**  
- ❌ **Avoid long text blocks that overwhelm users**

### Response Pattern Examples:

**User asks: "How many elements per building level?"**
❌ Long answer: *[3 paragraphs explaining the model, all categories, view details, etc.]*
✅ Short answer: "Can't see elements per level with current tools. Want to see total elements (49) or create a new analysis tool?"

**User asks: "What rooms are in the model?"**
❌ Long answer: *[Full furniture breakdown, room parameters, spatial organization, etc.]*
✅ Short answer: "6 rooms found. Want room names, furniture breakdown, or room areas?"

**User asks: "Can you place a door?"**
❌ Long answer: *[Explanation of family placement, all parameters, workflow steps, etc.]*
✅ Short answer: "Yes. Need door type first - want to see available doors or place at specific location?"

### Follow-up Suggestion Patterns:
- "Want to see [specific data]?"
- "Need [specific action] or [alternative]?"
- "Should I [concrete next step]?"
- "Create [specific tool/analysis] for this?"

### Family & Content Interpretation:
- ✅ **Default: "Families" = families in use in the model**
- ✅ **Clarify when showing project library vs. model content**
- ✅ **`list_families()` shows loaded families, not entire project**

### Category Resolution Architecture:
- ✅ **Three-layer system**: CategoryMapping.py → revit_nl_synonyms.json → fuzzy_category_matcher.py
- ✅ **Single source of truth**: Never duplicate category mappings
- ✅ **Fuzzy matching**: "kasten" → "Furniture", "deuren" → "Doors", typo tolerance
- ✅ **Priority handling**: "kasten" goes to Furniture (not Casework)
- ✅ **Confidence scoring**: >0.72 for fuzzy matches, 1.0 for exact matches

---

## 📋 Pre-Execution Checklist

### Before ANY Revit Tool Usage:
1. **Check Revit Status** - Always call `get_revit_status()` first
2. **Verify Character Encoding Safety** - All routes use `safe_string()` patterns
3. **Use Progressive Complexity** - Start simple, add complexity gradually
4. **Apply International Safety** - Assume European/accented characters exist

### Before ANY File Operations:
1. **Request Permission** - Always ask before writing/creating files
2. **Check Allowed Directories** - Use `list_allowed_directories()` first
3. **Validate Paths** - Ensure targets are within allowed locations

---

## 🛠️ Tool Categories & Usage

### A. Connection & Health Check Tools

#### 🔧 `get_revit_status()`
- **Purpose**: Verify Revit is running and document is available
- **When to use**: **ALWAYS FIRST** before any other Revit tool
- **Returns**: Health status, document title, API availability
- **Pattern**: 
```python
# ALWAYS start with this
status = await get_revit_status()
if "active" not in str(status):
    return "Revit is not available"
```

### B. Model Information & Analysis Tools

#### 🔧 `get_revit_model_info()`
- **Purpose**: Comprehensive model overview for architects
- **When to use**: Initial model assessment, project overview
- **Returns**: Project details, element counts, warnings, room info, linked models
- **Safe for**: International projects (uses encoding safety)

#### 🔧 `get_elements_by_category_level(category)`
- **Purpose**: Get elements of specific category grouped by level (efficient approach)
- **When to use**: When asking "how many X per level?" (doors, furniture, walls, etc.)
- **Category input**: Supports Dutch/English with fuzzy matching
- **Examples**: 'doors', 'deuren', 'walls', 'muren', 'kasten', 'meubilair'
- **Returns**: Element counts per level + elements without level
- **Important**: Uses correct level parameter per category (walls=Base Constraint, doors=Level)
- **Performance**: Efficient - filters category first, then checks levels

### C. View Tools

#### 🔧 `list_revit_views()`
- **Purpose**: Get all exportable views organized by type
- **When to use**: Before view capture, understanding available views
- **Returns**: Views grouped by type (floor plans, elevations, etc.)

#### 🔧 `get_current_view_info()`
- **Purpose**: Details about the currently active view
- **When to use**: Understanding current context, view analysis
- **Returns**: Scale, crop box, view type, discipline

#### 🔧 `get_current_view_elements()`
- **Purpose**: All elements visible in current view
- **When to use**: Analyzing view content, element inspection
- **Returns**: Element details grouped by category
- **⚠️ Note**: Can return large datasets - use for focused analysis

#### 🔧 `get_revit_view(view_name)`
- **Purpose**: Export specific view as PNG image
- **When to use**: Creating visual documentation, view captures
- **Returns**: Base64 encoded image data
- **Pattern**:
```python
# Always list views first to get exact names
views = await list_revit_views()
# Then use exact view name from the list
image = await get_revit_view("Ground Floor")
```

### D. Family & Placement Tools

#### 🔧 `list_families(contains=None, limit=50)`
- **Purpose**: Browse families **loaded and in use** in the model
- **When to use**: Before placement, understanding current content
- **Parameters**: 
  - `contains`: Filter by name substring
  - `limit`: Max results (default 50)
- **Returns**: Family name, type name, category, activation status
- **Important**: Shows only families **actively loaded** in model, not entire project library

#### 🔧 `list_family_categories()`
- **Purpose**: Overview of family categories with counts
- **When to use**: Understanding model content distribution

#### 🔧 `place_family(family_name, type_name, x, y, z, rotation, level_name, properties)`
- **Purpose**: Place family instances in the model
- **When to use**: Adding content programmatically
- **Required**: `family_name`
- **Optional**: All other parameters have defaults
- **⚠️ Transaction Safety**: Automatically handled with rollback on error
- **Pattern**:
```python
# Always verify family exists first
families = await list_families(contains="Door")
# Use exact names from the list
result = await place_family(
    family_name="Single-Flush", 
    type_name="0915 x 2134mm",
    level_name="Ground Floor"
)
```

### E. Specialized Analysis Tools

#### 🔧 `get_furniture_by_room()`
- **Purpose**: Room-based furniture inventory
- **When to use**: Space planning, furniture analysis
- **Returns**: Furniture grouped by room with family/type/mark
- **Safe for**: International projects (uses proper room parameter access)

---

## 🔄 Common Workflow Patterns

### 1. Model Initial Assessment
```python
# Standard model assessment sequence
1. get_revit_status()          # Verify connection
2. get_revit_model_info()      # Overall model info
3. list_levels()               # Spatial structure
4. list_revit_views()          # Available documentation
```

### 2. Content Analysis
```python
# Understanding model content
1. get_revit_status()
2. get_current_view_info()     # Current context
3. get_current_view_elements() # What's visible
4. list_families()             # Available content
```

### 3. Family Placement Workflow
```python
# Safe family placement
1. get_revit_status()
2. list_levels()               # Get valid level names
3. list_families(contains="target") # Find exact family names
4. place_family(...)           # Use exact names from above
```

### 4. Documentation Creation
```python
# View capture workflow
1. get_revit_status()
2. list_revit_views()          # Get available views
3. get_revit_view(exact_name)  # Use exact names from list
```

### 5. Room Analysis
```python
# Room-based analysis
1. get_revit_status()
2. get_revit_model_info()      # Includes room overview
3. get_furniture_by_room()     # Detailed room content
```

---

## ⚠️ Critical Safety Patterns

### Character Encoding Safety (CRITICAL for EU projects)
- **All routes use `safe_string()` functions**
- **Assume non-ASCII characters exist** (á, é, ü, etc.)
- **Test with European content early**
- **Never assume ASCII-only data**

### Unit Conversion Safety (CRITICAL for measurements)
- **Revit API uses internal units** (feet for length, square feet for area)
- **Always convert to project units** for user-friendly display
- **Use `UnitUtils.ConvertFromInternalUnits()` for display values**
- **Use `UnitUtils.ConvertToInternalUnits()` when setting values**
- **Include both internal and converted values in responses when helpful**

### Progressive Complexity Testing
1. **Start with Status Check** - `get_revit_status()`
2. **Test Simple Queries** - `list_levels()`, `list_revit_views()`
3. **Add String Data Gradually** - Room names, element names
4. **Monitor for Encoding Errors** - Watch for 'unknown codec' errors

### Error Pattern Recognition
- **`'unknown' codec can't decode byte`** → Encoding issue (use safe_string)
- **`result exceeds maximum length`** → Real size limit (use focused endpoints)
- **`Only 1 result when expecting many`** → Check for early return in loops
- **`No active Revit document`** → Revit connection lost

---

## 🚫 Tool Limitations & Restrictions

### Development Notes
- When creating new tools, **always ask to update this tool usage guide**
- New routes must include character encoding safety patterns
- All measurement values require unit conversion handling

### Size Limitations
- **Image exports**: Handled automatically (base64 encoding)
- **Element collections**: Use focused queries (current view vs. whole model)
- **Family lists**: Default limit 50, adjustable

### Transaction Safety
- **Family placement**: Automatically wrapped in transactions
- **All modifications**: Include rollback on error
- **Read operations**: No transaction needed

---

## 📁 File System Tools

### Always Ask Permission
- **Never write files without explicit permission**
- **Use `list_allowed_directories()` first**
- **Validate paths before operations**

### Available Operations
- `read_file()` - Read single file
- `read_multiple_files()` - Read several files efficiently  
- `write_file()` - Create/overwrite files (ASK PERMISSION)
- `edit_file()` - Line-based edits (ASK PERMISSION)
- `list_directory()` - Browse directory contents
- `directory_tree()` - Recursive structure view
- `search_files()` - Find files by pattern

---

## 🔧 Error Handling & Debugging

### Debugging Strategy
1. **Start Simple**: Test basic connectivity first
2. **Add Complexity Gradually**: Don't jump to complex queries
3. **Check Character Encoding**: Watch for non-ASCII content
4. **Use Exact Names**: Always get names from list functions first

### Common Fix Patterns
```python
# For encoding issues
room_name = safe_string(room.Name)

# For parameter safety
param_value = safe_parameter_value(parameter)

# For early returns in routes
for item in collection:
    process_item(item)
return result  # ← OUTSIDE the loop

# For family placement
families = await list_families(contains="Door")
# Use exact name from families list
```

### When Things Go Wrong
1. **Check Revit Connection**: `get_revit_status()`
2. **Verify Character Encoding**: Look for special characters
3. **Check Route Implementation**: Ensure no early returns in loops
4. **Test with Simpler Data**: Reduce complexity to isolate issue

---

## 🎯 Best Practices Summary

### Always Do
- ✅ Check `get_revit_status()` first
- ✅ Use exact names from list functions
- ✅ Request permission before writing files
- ✅ Handle international character sets
- ✅ Start simple, add complexity gradually
- ✅ Use progressive testing approach

### Never Do
- ❌ Skip status checks before Revit operations
- ❌ Assume ASCII-only content
- ❌ Write files without permission
- ❌ Use hardcoded view/family names without verification
- ❌ Ignore encoding safety patterns

### When Adding New Routes
- **ASK TO UPDATE THIS TOOL USAGE GUIDE** when creating new tools
- Include `safe_string()` and `safe_parameter_value()` functions
- Apply unit conversion for all measurement values
- Test with European characters early
- Use proper filtering (`.WhereElementIsNotElementType()`)
- Ensure return statements are outside loops
- Include proper error handling with rollback
- Document the new tool's purpose, usage, and safety considerations

---

## 📞 Quick Reference

### Essential First Commands
```python
status = await get_revit_status()        # Always first
info = await get_revit_model_info()      # Model overview  
levels = await list_levels()             # Spatial structure
views = await list_revit_views()         # Available views
```

### Family Workflow
```python
families = await list_families(contains="Door")  # Find families
result = await place_family("exact_name")        # Use exact names
```

### Analysis Workflow  
```python
current = await get_current_view_info()      # Current context
elements = await get_current_view_elements()  # What's visible
furniture = await get_furniture_by_room()     # Room-based content
```

This guide ensures safe, efficient, and reliable operation of the Revit MCP system while preventing the character encoding issues that plagued earlier development phases.