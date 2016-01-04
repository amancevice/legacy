module Pooler
  class Category < ActiveRecord::Base
    has_many :options
    has_many :picks

    default_scope -> { order :index }

    before_validation do
      last = Category.last
      self.index ||= last.nil? ? 0 : last.index + 1
    end

    def next
      Category.where( 'index > ?', self.index ).first
    end
  end
end
