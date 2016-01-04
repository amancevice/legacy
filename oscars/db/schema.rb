# encoding: UTF-8
# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# Note that this schema.rb definition is the authoritative source for your
# database schema. If you need to create the application database on another
# system, you should be using db:schema:load, not running all the migrations
# from scratch. The latter is a flawed and unsustainable approach (the more migrations
# you'll amass, the slower it'll run and the greater likelihood for issues).
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema.define(version: 20150222160312) do

  # These are extensions that must be enabled in order to support this database
  enable_extension "plpgsql"

  create_table "categories", force: :cascade do |t|
    t.integer "index"
    t.string  "name"
    t.integer "points"
  end

  create_table "options", force: :cascade do |t|
    t.integer "category_id"
    t.string  "type"
    t.string  "name"
    t.string  "subtitle"
    t.boolean "correct"
    t.integer "points"
  end

  create_table "picks", force: :cascade do |t|
    t.integer  "user_id"
    t.integer  "category_id"
    t.integer  "option_id"
    t.string   "pick"
    t.boolean  "correct"
    t.integer  "points"
    t.integer  "bonus"
    t.integer  "penalty"
    t.datetime "created_at",  null: false
    t.datetime "updated_at",  null: false
  end

  create_table "users", force: :cascade do |t|
    t.boolean  "admin"
    t.string   "username"
    t.string   "email"
    t.string   "first_name"
    t.string   "last_name"
    t.string   "password_hash"
    t.string   "salt"
    t.boolean  "locked"
    t.boolean  "paid"
    t.datetime "created_at",    null: false
    t.datetime "updated_at",    null: false
  end

end
