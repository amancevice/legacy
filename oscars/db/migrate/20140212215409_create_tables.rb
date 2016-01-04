class CreateTables < ActiveRecord::Migration
  def change
    Pooler.migrate
  end
end