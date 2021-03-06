# lib/bolton.rb
require "bolton/version"
require "bolton/alias"
require "bolton/export"

module Bolton
  ##
  # Class extending the existing bash profile
  class Profile
    attr_reader :shortname, :name, :source, :aliases, :exports

    ##
    # Creates a new Bolt-On profile
    #
    # +args+:: +Hash+ of optional arguments:
    #   +name+:: name of the profile to export to ~/ (will be prefixed with '.') [default: bolton]
    #   +source+:: name of the profile sourced at session start [default: .bashrc]
    #   +overwrite+:: overwrite any existing profiles with the same name instead of parsing first [default: false]
    def initialize args={}
      @shortname = args[:name]||'bolton'
      @name      = name_to_path @shortname
      @source    = name_to_path args[:source]||'.bashrc'
      @aliases   = []
      @exports   = []

      parse_existing unless args[:overwrite]||false
    end

    ##
    # Parses an existing profile to maintain any existing settings
    def parse_existing
      existing_contents.split(/[\r\n]+/).each do |line|
        if line =~ /\Aalias /
          @aliases << Bolton::Alias.parse(line)
        elsif line =~ /\Aexport /
          @exports << Bolton::Export.parse(line)
        end
      end
    end

    ##
    # Returns the content of the profile as a string
    def content
      out =  ["# --- Bolt-On-generated profile --- #"]
      out << ["# .#{@shortname}"]
      out << ''
      @aliases.map{|x| out << x.content }
      @exports.map{|x| out << x.content }

      out.join("\n")
    end

    ##
    # Saves the profile to disk
    def save
      File.open(@name, 'w'){|f| f.write self.to_s }
    end

    ##
    # Add an alias to the profile
    #
    # +name+:: name of the alias
    # +val+:: the alias to assign
    #   profile = Bolton::Profile.new name:'my_profile'
    #   profile.alias 'wow', 'git add -p'
    #   # => alias wow='git add -p'
    def alias name, val
      @aliases << Bolton::Alias.new(name, val)
    end

    ##
    # Add export to the profile
    #
    # +name+:: name of the variable
    # +val+:: value of the variable
    # +type+:: optional argument to indicate prepending/extending an existing export
    #
    #   profile = Bolton::Profile.new name:'my_profile'
    #   profile.export 'PATH', '/path/to/path', :extend
    #   # => export PATH=$PATH:/path/to/path
    def export name, val, type=nil
      @exports << Bolton::Export.new(name, val, type)
    end

    ##
    # Attaches the custom profile to the source profile
    #
    # # --- Autogenerated by Bolt-On gem -- #
    # if [ -f ~/.my_profile ]; then
    #   . ~/.my_profile
    # fi
    # # --- End of Bolt-On --- #
    def attach
      instructions =  ['# --- Autogenerated by Bolt-On gem -- #']
      instructions << ["if [ -f #{@name} ]; then"]
      instructions << ["  . #{@name}"]
      instructions << ['fi']
      instructions << ['# --- End of Bolt-On --- #']
      instructions =  "\n" + instructions.join("\n") + "\n"
      current_profile = File.read @profile_filename

      unless current_profile.include? instructions
        current_profile += instructions

        File.open(@profile_filename, 'w') do |f|
          f.write current_profile
        end
      end
    end

    private

    ##
    # Converts a profile name to path
    def name_to_path name
      name.to_s[0] == '.' ? "#{ENV['HOME']}/#{name}" : "#{ENV['HOME']}/.#{name}"
    end

    ##
    # Gets the existing contents of the custom profile
    def existing_contents
      File.exists?(@name) ? File.read(@name) : ''
    end
  end
end
