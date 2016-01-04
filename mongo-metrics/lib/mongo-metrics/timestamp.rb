# Copyright (c) 2013 ICRL
#
# See the file license.txt for copying permission.

module MongoMetrics
  #
  # Simple wrapper for handling Java-style epoch timestamps
  #
  class Timestamp

    SECONDS_MOD = 10000000000

    def self.at( timestamp_string )
      timestamp = timestamp_string.to_i
      timestamp = timestamp / 1000 unless timestamp % SECONDS_MOD == timestamp

      Time.at timestamp
    end
  end
end