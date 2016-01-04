# Copyright (c) 2013 ICRL
#
# See the file license.txt for copying permission.

module MongoMetrics
  class Config
    include Mongo

    def self.mongo( env=:development )
      config = YAML.load(File.read('config/database.yml'))[env.to_s]
      unless config.nil?
        MongoMapper.connection = Mongo::Connection.new config['host'], config['port']
        MongoMapper.database   = config['database']
        $db = MongoMapper.database
        $db.connection.drop_database config['database']
      end
    end

    def self.metrics
      $metric_types = {}
      metric_yaml = YAML.load File.read('config/metric_types.yml')
      metric_yaml.each do |type, definition|
        raise ArgumentError.new("Malformed Config file: No definition for #{type} metric type") if definition.nil? || definition.empty?

        # Metric Interval
        interval = definition['interval']
        raise ArgumentError.new("Malformed Config file: No interval for #{type} metric") if interval.nil? || interval.empty?

        # Column order for STDIN
        columns = definition['columns']
        raise ArgumentError.new("Malformed Config file: No columns for #{type} metric") if columns.nil? || columns.empty?

        # Dimensions for aggregating (optional)
        dimensions = definition['dimensions']

        # Aggregation measures
        measures = definition['measures']
        raise ArgumentError.new("Malformed Config file: No measures for #{type} metric") if measures.nil? || measures.empty?

        # Create Aggregate Classes
        aggregate_classes = []
        measures.each do |measure|
          measure_name = measure.keys.first
          aggregate_class_name = type.camelize+measure_name.camelize
          aggregate_class = Object.const_set aggregate_class_name, Class.new
          aggregate_class.class_eval do
            include MongoMapper::Document
            key :type,           String
            key :interval_group, Integer
            key :count,          Integer
            dimensions.map{|dim| key dim.to_sym, String }
            measure.each do |measure_name,methods|
              methods.map{|method| key (measure_name+'_'+method).to_sym, Float }
            end
          end
          $logger.info "Created #{aggregate_class_name} Class"
          aggregate_classes << aggregate_class
        end

        # Create Metric Class
        metric_class_name = type.camelize
        metric_class = Object.const_set metric_class_name, Class.new
        metric_class.class_eval do
          include MongoMapper::Document
          safe
          key :type,           String,  :required => true
          key :timestamp,      Integer, :required => true
          key :interval_group, Integer, :required => true
          dimensions.map{|dim| key dim.to_sym, String }
          measures.map{|measure| key measure.keys.first.to_sym, Float }

          def self.aggregate( interval_group, dimensions, measure )
            measure_name = measure.keys.first
            ids = {}; dimensions.map{|m| ids[m] = '$'+m }
            match = { '$match' => { 'interval_group' => interval_group } }
            group = { '$group' => { '_id' => ids } }
            measure.values.flatten.map{|x| group['$group'][measure_name+'_'+x] = { '$'+x => '$'+measure_name } }

            self.collection.aggregate [match, group]
          end
        end
        $logger.info "Created #{metric_class_name} Class"

        # Metric Finder Helper
        $metric_types[type] = {
          :metric_class      => metric_class,
          :aggregate_classes => aggregate_classes,
          :interval          => Rufus.parse_time_string(interval),
          :columns           => columns,
          :dimensions        => dimensions,
          :measures          => measures
        }
      end
    end
  end
end