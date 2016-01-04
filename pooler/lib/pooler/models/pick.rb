module Pooler
  class Pick < ActiveRecord::Base
    belongs_to :user
    belongs_to :category
    belongs_to :option

    default_scope     -> { joins(:category).order('categories.index').order(:pick) }
    scope :correct,   -> { where correct:true    }
    scope :incorrect, -> { where correct:false   }
    scope :decided,   -> { where.not correct:nil }
    scope :undecided, -> { where correct:nil     }

    before_validation do
      self.option ||= self.category.options.first
      self.pick   ||= option.name
    end

    def inspect;    "#<Pick: \"#{self}\", points: #{self.points}, bonus: #{self.bonus||'nil'}, penalty: #{self.penalty||'nil'} >"; end
    def correct!;   self.correct = true;  self.save; end
    def incorrect!; self.correct = false; self.save; end
    def reset!;     self.correct = nil;   self.save; end
    def correct?;   self.correct == true;  end
    def incorrect?; self.correct == false; end

    def pick
      # TODO begin/rescue here?
      self.option.interpret read_attribute(:pick)
    end

    def to_s
      self.option.display read_attribute(:pick)
    end

    def points type=:actual||:potential
      points = read_attribute(:points)||self.option.points
      type == :actual && self.incorrect? ? (self.penalty||0) : points + (self.bonus||0)
    end
  end
end
