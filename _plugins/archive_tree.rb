# Local Jekyll and hosted builds use the same folder-to-metadata synchronization.
require 'open3'

Jekyll::Hooks.register :site, :after_reset do |site|
  script = File.join(site.source, 'scripts', 'prepare_archive.py')
  output, error, status = Open3.capture3(ENV.fetch('ARCHIVE_PYTHON', 'python'), script, '--root', site.source)
  unless status.success?
    raise Jekyll::Errors::FatalException, "Archive hierarchy: #{output}\n#{error}"
  end
end

# One physical archive, three logical collections for existing site templates.
Jekyll::Hooks.register :site, :post_read do |site|
  works = site.collections['works']
  next unless works
  profiles, documents = works.docs.partition { |doc| %w[author collection].include?(doc.data['record_type']) }
  works.docs.replace(documents)
  profiles.each do |source|
    kind = source.data['record_type'] == 'author' ? 'authors' : 'zbirke'
    collection = site.collections[kind]
    document = Jekyll::Document.new(source.path, site: site, collection: collection)
    document.read
    collection.docs << document
  end
end
