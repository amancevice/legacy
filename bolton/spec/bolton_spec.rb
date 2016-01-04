# spec/bolton_spec.rb
require 'bolton'

describe Bolton::Profile do
  existing_source_content = ""
  existing_content = "# --- Bolt-On-generated profile --- #\n# .bolton\n\nalias foo='bar --help'\nexport BAZ=/path/to/somewhere:$BAZ"
  existing_path    = "#{ENV['HOME']}/.bolton-test"
  existing_source  = "#{ENV['HOME']}/.bashrc-test"

  before do
    File.open(existing_path, 'w') {|f| f.write existing_content }
    File.open(existing_source, 'w') {|f| f.write existing_source_content }
  end

  after do
    File.delete existing_path
    File.delete existing_source
  end

  describe '#parse_existing' do
    it 'should parse an existing profile' do
      profile = Bolton::Profile.new name:'.bolton-test'
      profile.aliases.first.name.should eq('foo')
      profile.aliases.first.val.should eq("'bar --help'")
      profile.exports.first.name.should eq('BAZ')
      profile.exports.first.val.should eq('/path/to/somewhere:$BAZ')
    end
  end

  describe '#content' do
    it 'should return the contents of the generated profile' do
      content = "# --- Bolt-On-generated profile --- #\n# .bolton\n\nalias foo='bar --help'\nexport BAZ=/path/to/somewhere:$BAZ"
      profile = Bolton::Profile.new
      profile.alias 'foo', 'bar --help'
      profile.export 'BAZ', '/path/to/somewhere', :prepend
      profile.content.should eq(content)
    end
  end

  describe '#save' do
  end

  describe '#alias' do
    it "should alias 'foo' to 'bar --help" do
      profile = Bolton::Profile.new
      profile.alias 'foo', 'bar --help'
      profile.aliases.first.name.should eq('foo')
      profile.aliases.first.val.should eq("'bar --help'")
    end
  end

  describe '#export' do
    it "should export 'BAZ' to '/path/to/somewhere'" do
      profile = Bolton::Profile.new
      profile.export 'BAZ', '/path/to/file'
      profile.exports.first.name.should eq('BAZ')
      profile.exports.first.val.should eq('/path/to/file')
    end

    it "should export 'BAZ' to '/path/to/somewhere:BAZ'" do
      profile = Bolton::Profile.new
      profile.export 'BAZ', '/path/to/file', :prepend
      profile.exports.first.name.should eq('BAZ')
      profile.exports.first.val.should eq('/path/to/file:$BAZ')
    end
  end

  describe '#attach' do
  end

  describe '#name_to_path' do
    it 'should convert a profile name to a path' do
      profile = Bolton::Profile.new
      path = profile.send(:name_to_path, 'bolton')
      path.should eq("#{ENV['HOME']}/.bolton")
    end
  end
end