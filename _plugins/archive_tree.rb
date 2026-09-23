# Local Jekyll and hosted builds use the same folder-to-metadata synchronization.
require 'open3'

Jekyll::Hooks.register :site, :after_reset do |site|
  script = File.join(site.source, 'scripts', 'prepare_archive.py')
  output, error, status = Open3.capture3(ENV.fetch('PYTHON', 'python'), script, '--root', site.source)
  unless status.success?
    raise Jekyll::Errors::FatalException, "Archive hierarchy: #{output}\n#{error}"
  end
end
