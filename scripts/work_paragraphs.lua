-- Keep single source newlines tight, with prose indents in PDFs; reserve
-- explicit blank lines for paragraph gaps.
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
  local in_work = true

  for _, block in ipairs(document.blocks) do
    if block.t == 'Header' and block.classes:includes('archive-note') then
      poetry = false
      in_work = false
    end

    if block.t == 'CodeBlock' and block.classes:includes('verse') then
      local lines = {}
      for line in (block.text .. '\n'):gmatch('(.-)\n') do
        table.insert(lines, pandoc.Inlines({pandoc.Str(line)}))
      end
      blocks:insert(pandoc.LineBlock(lines))
    elseif block.t == 'Para' and poetry then
      local lines = split_lines(block.content)
      blocks:insert(pandoc.LineBlock(lines))
    elseif block.t == 'Para' and in_work and FORMAT == 'latex' then
      local content = pandoc.Inlines({})
      for index, line in ipairs(split_lines(block.content)) do
        if index > 1 then
          content:insert(pandoc.LineBreak())
          content:insert(pandoc.RawInline('latex', '\\hspace*{\\parindent}'))
        end
        content:extend(line)
      end
      blocks:insert(pandoc.Para(content))
    else
      blocks:insert(block)
    end
  end

  document.blocks = blocks
  return document
end
