# lib/bolton/alias.rb
module Bolton
  ##
  # Profile alias
  class Alias
    attr_accessor :name, :val

    ##
    # Initializes an alias
    #
    # +name+:: name of the alias
    # +val+:: the alias to assign
    def initialize name, val
      @name = name
      @val  = "'#{val}'".sub(/\A''/,"'").sub(/''\Z/,"'")
    end

    ##
    # Gets content to write to profile
    def content
      "alias #{@name}=#{@val}"
    end

    class << self
      ##
      # Parses an existing alias into a Bolton::Alias object
      def parse line
        match = line.match /alias (.*?)=(.*)\Z/
        name  = match[1].strip
        val   = match[2].strip

        Bolton::Alias.new name, val
      end
    end
  end
end