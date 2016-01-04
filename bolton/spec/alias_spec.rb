# spec/alias_spec.rb
require 'bolton'

describe Bolton::Alias do
  describe '#content' do
    it "returns \"alias foo='bar --help'\"" do
      alias_ = Bolton::Alias.new 'foo', 'bar --help'
      alias_.content.should eq("alias foo='bar --help'")
    end
  end

  describe "::parse" do
    it "returns new Bolton::Alias with foo='bar --help'" do
      export = Bolton::Alias.parse "alias foo='bar --help'"
      export.name.should eq('foo')
      export.val.should eq("'bar --help'")
    end
  end
end
