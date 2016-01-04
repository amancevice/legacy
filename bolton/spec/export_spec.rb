# spec/export_spec.rb
require 'bolton'

describe Bolton::Export do
  describe '#content' do
    it "should return 'export FOO=bar'" do
      export = Bolton::Export.new 'foo', 'bar'
      export.content.should eq('export FOO=bar')
    end

    it "should return 'export FOO=bar:FOO'" do
      export = Bolton::Export.new 'foo', 'bar', :prepend
      export.content.should eq('export FOO=bar:$FOO')
    end

    it "should return 'export FOO=FOO:bar'" do
      export = Bolton::Export.new 'foo', 'bar', :extend
      export.content.should eq('export FOO=$FOO:bar')
    end
  end

  describe '::parse' do
    it 'should return new Bolton::Export with FOO=bar' do
      export = Bolton::Export.parse 'export FOO=bar'
      export.name.should eq('FOO')
      export.val.should eq('bar')
    end

    it 'should return new Bolton::Export with FOO=bar' do
      export = Bolton::Export.parse 'export FOO=bar:$FOO'
      export.name.should eq('FOO')
      export.val.should eq('bar:$FOO')
    end

    it 'should return new Bolton::Export with FOO=bar' do
      export = Bolton::Export.parse 'export FOO=$FOO:bar'
      export.name.should eq('FOO')
      export.val.should eq('$FOO:bar')
    end
  end
end
