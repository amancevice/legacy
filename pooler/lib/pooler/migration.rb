require 'active_record'

module Pooler

  def self.migrate
    begin
      Pooler::Migration::Users.new.change
      Pooler::Migration::Pooler.new.change
    rescue ActiveRecord::ConnectionNotEstablished
      # TODO This should probably do something more meaningful
      puts "No Connection"
    end
  end

  module Migration

    class Pooler < ActiveRecord::Migration
      def change
        create_table :categories do |t|
          t.integer    :index     # Category order
          t.string     :name      #   * Best Actor
          t.integer    :points    # Category has a set point value?
        end

        create_table :options do |t|
          t.belongs_to :category
          t.string     :type      # tells the Pick how to interpret :pick
          t.string     :name      #   * Gary Oldman
          t.string     :subtitle  #   * Tinker Tailor Soldier Spy
          t.boolean    :correct   # true/false/nil
          t.integer    :points    # Option has a set point value?
        end

        create_table :picks do |t|
          t.belongs_to :user
          t.belongs_to :category
          t.belongs_to :option
          t.string     :pick      # What is the user actually choosing
          t.boolean    :correct   # true/false/nil
          t.integer    :points    # How many points is the pick worth?
          t.integer    :bonus     # + point bonus
          t.integer    :penalty   # - point penalty
          t.timestamps null:false
        end
      end
    end

    class Users < ActiveRecord::Migration
      def change
        create_table :users do |t|
          t.boolean    :admin
          t.string     :username
          t.string     :email
          t.string     :first_name
          t.string     :last_name
          t.string     :password_hash
          t.string     :salt
          t.boolean    :locked
          t.boolean    :paid
          t.timestamps null:false
        end
      end
    end

  end
end
