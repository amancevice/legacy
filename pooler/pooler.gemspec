# coding: utf-8
lib = File.expand_path('../lib', __FILE__)
$LOAD_PATH.unshift(lib) unless $LOAD_PATH.include?(lib)
require 'pooler/version'

Gem::Specification.new do |spec|
  spec.name          = "pooler"
  spec.version       = Pooler::VERSION
  spec.authors       = ["Small Weird Number"]
  spec.email         = ["smallweirdnum@gmail.com"]
  spec.summary       = %q{The makings for a betting pool.}
  spec.description   = %q{An ActiveRecord baseline.}
  spec.homepage      = ""
  spec.license       = "MIT"

  spec.files         = `git ls-files -z`.split("\x0")
  spec.executables   = spec.files.grep(%r{^bin/}) { |f| File.basename(f) }
  spec.test_files    = spec.files.grep(%r{^(test|spec|features)/})
  spec.require_paths = ["lib"]

  spec.add_runtime_dependency "activerecord"
  spec.add_runtime_dependency "bcrypt"

  spec.add_development_dependency "bundler", "~> 1.7"
  spec.add_development_dependency "rake", "~> 10.0"
end
