class Users < ActiveRecord::Migration
  def change
    Pooler::User.all.each do |user|
      user.password = user.email
      user.email = user.username
      user.save!
    end
  end
end
