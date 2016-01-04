require 'bundler/setup'
Bundler.require
require 'securerandom'

require 'yaml'

class Oscars < Sinatra::Base
  set :root, File.dirname(__FILE__)
  enable :sessions
  helpers  Sinatra::Cookies
  register Sinatra::AssetPack
  register Sinatra::ActiveRecordExtension
  register Sinatra::Flash
  I18n.config.enforce_available_locales = true

  assets do
    js  :app, [ '/js/*.js' ]
    css :app, [ '/css/*.css' ]

    js_compression  :jsmin
    css_compression :sass
  end

  before do
    unless request.path_info =~ /\A\/(login|signup|css)\/?/
      @user = Pooler::User.find_by username:session[:user]
      redirect '/login' if @user.nil?
    end
  end

  get '/' do
    erb :index
  end

  #
  # Authentication
  #

  get '/login' do
    erb :login
  end

  get '/signup' do
    erb :signup
  end

  get '/logout' do
    @user = nil
    session[:user] = nil
    redirect '/'
  end

  post '/login' do
    @user = Pooler::User.find_by username:params[:name]

    if @user.nil?
      flash[:error] = "Couldn\'t find #{params[:email]}. Try again or sign up."
      redirect '/login'
    elsif !@user.login(params[:password])
      flash[:error] = 'There was a problem signing in. Try again.'
      redirect '/login'
    end

    session[:user] = @user.username
    redirect session[:redirect]||'/'
  end

  post '/signup' do
    # Match passwords
    unless params[:password] == params[:confirm_password]
      flash[:error] = 'Passwords do not match. Try again.'
      redirect '/signup'
    end

    # Sign up
    @user = Pooler::User.signup params[:username], params[:email], params[:password]

    # Validate
    unless @user.errors.empty?
      flash[:error] = "That name/email was rejected for the following reasons:<br />&nbsp;&nbsp;&nbsp;#{@user.errors.full_messages.join "<br />&nbsp;&nbsp;&nbsp;"}"
      redirect '/signup'
    end

    # Log in
    session[:user] = @user.username

    redirect '/'
  end

  #
  # Pool
  #

  get '/admin' do
    redirect '/' unless @user.admin?
    @admin = true
    erb :admin
  end

  get '/admin/:user/paid' do |user|
    user = Pooler::User.find_by username:URI::decode(user)
    user.paid? ? user.update!(paid:nil) : user.pay!
    redirect '/admin'
  end

  get '/admin/:category/:option' do |category, option|
    @category = Pooler::Category.find_by name:URI::decode(category)
    unless @category.nil?
      @option  = @category.options.find_by name:URI::decode(option)
      unless @option.nil?
        if @option.correct?
          @option.reset!
        else
          @category.options.where.not(id:@option.id).collect(&:incorrect!)
          @option.correct!
        end
      end
    end
    redirect '/admin'
  end

  get '/picks' do
    @user_ = @user
    erb :picks
  end

  get '/leaderboard' do
    erb :leaderboard
  end

  get '/users/:username' do |username|
    username = URI::decode username
    @user_   = Pooler::User.find_by username:username
    erb :review
  end

  get '/pay' do
    erb :pay
  end

  get '/submit' do
    @user.lock!
    flash[:info] = "Thanks for playing. Now pay up!"
    redirect '/pay'
  end

  get '/:category' do |category|
    category  = URI::decode category
    @category = Pooler::Category.find_by name:category
    erb :category unless @category.nil?
  end

  get '/:category/:option' do |category, option|
    redirect "#{category}" if @user.locked?
    @category = Pooler::Category.find_by name:URI::decode(category)
    unless @category.nil?
      @option = @category.options.find_by name:URI::decode(option)
      unless @option.nil?
        @user.picks.where(category:@category).delete_all
        @pick = @user.picks.create( category: @category,
                                    option:   @option,
                                    pick:     @option.name,
                                    points:   @option.points )
        redirect "#{category}"
      end
    end
  end

  get '/:category/:option/gild' do |category, option|
    @category = Pooler::Category.find_by name:URI::decode(category)
    unless @category.nil?
      @option = @category.options.find_by name:URI::decode(option)
      unless @option.nil?
        @pick = @user.picks.find_by category:@category, option:@option
        @pick.update bonus:@pick.points, penalty:-@pick.points

        bonus    = @pick.points :potential
        penalty  = @pick.penalty
        message  = "<strong>Gilded!</strong>"
        message += "<br />If <em>#{@pick.pick}</em> wins, you will gain <strong>#{bonus} "
        message += bonus.abs == 1 ? "point</strong>. " : "points</strong>. "
        message += "If it loses, you will lose <strong>#{@pick.penalty} "
        message += penalty.abs == 1 ? "point</strong>. " : "points</strong>. "
        message += "<br />Click your choice again to return it to normal."
        puts message
        flash[:info] = message
        redirect "#{URI::encode category}"
      end
    end
  end
end
