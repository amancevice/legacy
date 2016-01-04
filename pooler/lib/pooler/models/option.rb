module Pooler
  class Option < ActiveRecord::Base
    belongs_to :category
    has_many   :picks

    default_scope     -> { order(points: :desc).order :name }
    scope :correct,   -> { where id:select{|x| x.correct?   }.collect(&:id) }
    scope :incorrect, -> { where id:select{|x| x.incorrect? }.collect(&:id) }

    def points
      read_attribute(:points)||self.category.points
    end

    def correct!;   self.correct = true;  self.save; self.picks.collect(&:correct!);   end
    def incorrect!; self.correct = false; self.save; self.picks.collect(&:incorrect!); end
    def reset!;     self.correct = nil;   self.save; self.picks.collect(&:reset!);     end
    def correct?;   self.correct == true  || self.picks.correct.any?;   end
    def incorrect?; self.correct == false || self.picks.incorrect.any?; end

    def interpret(value); value.to_s; end
    def display(value); self.interpret value; end
  end

  class DateOption < Option
    def interpret(value); value.to_date; end
    def display(value); super(value).strftime('%B %-d, %Y'); end
  end

  class DateTimeOption < Option
    def interpret(value); value.to_datetime; end
    def display(value); super(value).strftime('%B %-d, %Y %l:%M%P'); end
  end

  class TimeOption < Option
    # Minutes past midnight
    def interpret(value); value.to_i; end
    def display(value); (Date.today.to_datetime + super(value)).strftime('%l:%M%P'); end
  end
end
