config = YAML.load_file('./config/nominees.yaml')

config.each do |category,options|
  category = Pooler::Category.find_or_create_by name:category
  options.map{|x| Pooler::Option.find_or_create_by **x.symbolize_keys.merge(category:category) }
end

admin = Pooler::User.find_by username:'Alexander Mancevice'
admin = Pooler::User.signup 'Alexander Mancevice', 'alex@swn.com', 'aaaa' if admin.nil?
admin.admin = true
admin.save!

Pooler::Category.all.each do |category|
  option = category.options.shuffle.first
  pick = admin.picks.new( category: category,
                          option:   option,
                          pick:     option.name,
                          points:   option.points )
  if rand(0..2) == 0
    pick.bonus   = option.points
    pick.penalty = -option.points
  end
  pick.save
end