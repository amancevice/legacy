# Pooler

Foundation ActiveRecord definitions for building a better betting pool. Provides an interface for managing Users, Categories, Options, & Picks.

A Category is a scorable set of options.

An Option is a value-choice for a given category. An option could be a static or a class of choices that the user decided.

A Pick is the actual value chosen by the user with a point value attached to the pick and an optional bonus/penalty.

## Installation

Add this line to your application's Gemfile:

```ruby
gem 'pooler'
```

And then execute:

    $ bundle

Or install it yourself as:

    $ gem install pooler

## Usage

Create your pool's Categories

```ruby
best_actress = Pooler::Category.create name:'Best Actress'
start_time   = Pooler::Category.create name:'Oscars Start Time'
bonus_word   = Pooler::Category.create name:'Bonus Word',  points:10
my_birthday  = Pooler::Category.create name:'My Birthday', points:10
```

Create Options for each category

```ruby
# Static Options
best_actress.options << Pooler::Option.new name:'Marion Cotillard',  subtitle : 'Two Days, One Night',      points   : 5
best_actress.options << Pooler::Option.new name:'Felicity Jones',    subtitle : 'The Theory of Everything', points   : 5
best_actress.options << Pooler::Option.new name:'Rosamund Pike',     subtitle : 'Gone Girl',                points   : 3
best_actress.options << Pooler::Option.new name:'Reese Witherspoon', subtitle : 'Wild',                     points   : 3
best_actress.options << Pooler::Option.new name:'Julianne Moore',    subtitle : 'Still Alice',              points   : 1

# Time Option
start_time.options << Pooler::TimeOption.new name:'Start Time of First Award'

# Custom Option
bonus_word.options << Pooler::Option.new name:'Presenter Bonus Word', subtitle: 'Earn a point for each time the word is uttered'

# Date Option
my_birthday.options << Pooler::DateOption.new name:'My Birthday'
```

Create Picks for each category

```ruby
user.picks << Pooler::Pick.new category:best_actress, option:julianne_moore # :pick defaults to option.name
user.picks << Pooler::Pick.new category:start_time                          # :option defaults to start_time.options.first
user.picks << Pooler::Pick.new category:bonus_word, pick:'Korea'
user.picks << Pooler::Pick.new category:my_birthday, pick:'1900-01-01'
```

## Contributing

1. Fork it ( https://github.com/[my-github-username]/pooler/fork )
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create a new Pull Request
