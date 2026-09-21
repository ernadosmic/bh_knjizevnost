-- Match the website: each prose line is a paragraph, verse keeps its lines.
local function split_lines(inlines)
  local lines = {pandoc.Inlines({})}
  for _, inline in ipairs(inlines) do
    if inline.t == 'LineBreak' or inline.t == 'SoftBreak' then
      table.insert(lines, pandoc.Inlines({}))
    elseif inline.content and inline.t ~= 'Note' then
      for index, part in ipairs(split_lines(inline.content)) do
        if index > 1 then table.insert(lines, pandoc.Inlines({})) end
        local copy = inline:clone()
        copy.content = part
        lines[#lines]:insert(copy)
      end
    else
      lines[#lines]:insert(inline)
    end
  end
  return lines
end

function Pandoc(document)
  local work_type = document.meta['work-type']
  local poetry = work_type and pandoc.utils.stringify(work_type) == 'poetry'
  local blocks = pandoc.Blocks({})
  local previous_was_prose = false
  local previous_was_header = false

  for _, block in ipairs(document.blocks) do
    if block.t == 'Header' and block.classes:includes('archive-note') then
      poetry = false
    end
    if block.t == 'CodeBlock' and block.classes:includes('verse') then
      local lines = {}
      for line in (block.text .. '\n'):gmatch('(.-)\n') do
        table.insert(lines, pandoc.Inlines({pandoc.Str(line)}))
      end
      blocks:insert(pandoc.LineBlock(lines))
      previous_was_prose = false
      previous_was_header = false
    elseif block.t == 'Para' then
      local lines = split_lines(block.content)
      if poetry then
        blocks:insert(pandoc.LineBlock(lines))
        previous_was_prose = false
        previous_was_header = false
      else
        if previous_was_prose and not previous_was_header then
          blocks:insert(pandoc.RawBlock('latex', '\\addvspace{1.3em}'))
        end
        for index, line in ipairs(lines) do
          if #line > 0 then
            if index > 1 and not previous_was_header then
              blocks:insert(pandoc.RawBlock('latex', '\\addvspace{1.3em}'))
            end
            blocks:insert(pandoc.Para(line))
          end
        end
        previous_was_prose = true
        previous_was_header = false
      end
    else
      blocks:insert(block)
      previous_was_prose = false
      previous_was_header = block.t == 'Header'
    end
  end
  document.blocks = blocks
  return document
end
