# lib/bolton/export.rb
module Bolton
  ##
  # Profile export
  class Export
    attr_accessor :name, :val

    ##
    # Initializes an export
    #
    # +name+:: name of the export
    # +val+:: the value of the export
    # +type+:: :prepend/:entend for existing export
    def initialize name, val, type=nil
      @name = name.to_s.upcase
      @val  = val
      if type == :prepend
        @val = [@val, "$#{@name}"].join ':'
      elsif type == :extend
        @val = ["$#{@name}", @val].join ':'
      end
    end

    ##
    # Gets content to write to profile
    def content
      "export #{@name}=#{val}"
    end

    class << self
      ##
      # Parses an existing export into a Bolton::Alias object
      def parse line
        match = line.match /export (.*?)=(.*)\Z/
        name  = match[1].strip
        val   = match[2].strip
        type  = nil # prepend (val:$NAME) or extend ($NAME:val)
        if val =~ /\$#{name}\Z/
          type = :prepend
          val  = val.split(/:/)[0..-2].join ':'
        elsif val =~ /\A\$#{name}/
          type = :extend
          val  = val.split(/:/)[1..-1].join ':'
        end

        Bolton::Export.new name, val, type
      end
    end
  end
end