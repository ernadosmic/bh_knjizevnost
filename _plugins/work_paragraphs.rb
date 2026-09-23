# Literary works use one source line per prose paragraph. Transform the parsed
# Markdown so headings, lists, code, and formatting retain their meaning.
require 'kramdown'
require 'kramdown-parser-gfm'

module WorkParagraphs
  # Match scripts/literary_markdown.py: dialogue dashes are literal text.
  def self.literal_dashes(source)
    fence = nil
    source.lines.map do |line|
      content = line.sub(/\A(?: {0,3}>[ \t]?)+/, '').chomp
      marker = content.match(/\A {0,3}(`{3,}|~{3,})(.*)\z/)
      if fence
        if marker && marker[1][0] == fence[0] && marker[1].length >= fence.length && marker[2].strip.empty?
          fence = nil
        end
      elsif marker
        fence = marker[1]
      elsif !content.match?(/\A {0,3}(?:-[ \t]*){3,}\z/)
        line = line.sub(/\A((?: {0,3}>[ \t]?)* {0,3})-(?=[ \t]|$)/) { "#{Regexp.last_match(1)}\\-" }
      end
      line
    end.join
  end

  def self.split_lines(children)
    lines = [[]]
    children.each do |child|
      if child.type == :br
        lines << []
      elsif child.children.empty?
        lines.last << child
      else
        split_lines(child.children).each_with_index do |part, index|
          lines << [] if index.positive?
          copy = child.dup
          copy.children = part
          lines.last << copy
        end
      end
    end
    lines
  end

  def self.render(source, poetry: false, options: {})
    document = Kramdown::Document.new(literal_dashes(source), **options.merge(input: 'GFM', hard_wrap: true))
    after_blank = false
    document.root.children = document.root.children.flat_map do |block|
      separated = after_blank
      after_blank = block.type == :blank
      if block.type == :codeblock && block.options[:lang] == 'verse'
        stanza = Kramdown::Element.new(:p, nil, { 'class' => 'verse' })
        block.value.lines(chomp: true).each_with_index do |line, index|
          stanza.children << Kramdown::Element.new(:br) if index.positive?
          stanza.children << Kramdown::Element.new(:text, line)
        end
        [stanza]
      elsif block.type == :p && poetry
        block.attr['class'] = [block.attr['class'], 'verse'].compact.join(' ')
        [block]
      elsif block.type == :p
        split_lines(block.children).reject(&:empty?).each_with_index.map do |line, index|
          paragraph = Kramdown::Element.new(:p, block.value, block.attr.dup, block.options.dup)
          if separated && index.zero?
            paragraph.attr['class'] = [paragraph.attr['class'], 'paragraph-gap'].compact.join(' ')
          end
          paragraph.children = line
          paragraph
        end
      else
        [block]
      end
    end
    document.to_html
  end
end

Jekyll::Hooks.register :documents, :pre_render do |document|
  next unless document.collection.label == 'works'

  options = document.site.config.fetch('kramdown', {}).transform_keys(&:to_sym)
  document.data['rendered_work'] = WorkParagraphs.render(
    document.content, poetry: document.data['type'] == 'poetry', options: options
  )
end
