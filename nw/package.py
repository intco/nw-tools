#!/usr/bin/env python
import os, sys
import subprocess
import shutil
import re

from nw import nwfiles
from nw import getnwfromnet
from nw import getlatestversion
from nw import is_win, is_darwin, is_linux, is_cygwin


_DIR_FOR_APP = 'nw-packaged-app'
_DIR_FOR_EXEC = 'exec-app'

ignore_dirs = [
  _DIR_FOR_APP,
]

def CheckVer(ver):
  match = '\d*.\d*.\d*'
  if re.match(match, ver):
    return True

  else:
    print 'The format of version %s is not corrent.' % (ver)
    return False


def MakeZip():
  """ compress the source code """

  tmp_cwd = os.getcwd()
  os.chdir(options['path_to_app_src'])

  app_name = options['app_name']
  top = '.'
  tmp_app_path = os.path.join(options['path_for_package'], app_name)

  print 'Begin to compress app.'
  """ copy files """
  if os.path.isdir(tmp_app_path):
    shutil.rmtree(tmp_app_path)
  
  fileList = []
  folderList = []
  
  for root, subFolders, files in os.walk(top):
      for sub_folder in subFolders:
        sub_folder_path = os.path.join(root, sub_folder)
        sub_folder_path = os.path.abspath(os.path.join(tmp_app_path, sub_folder_path))
        folderList.append(sub_folder_path);
        
      for file in files:
          fileList.append(os.path.join(root,file))

  
  if options['slimit']:
    from slimit import minify

  os.mkdir(tmp_app_path)
  
  for fld in folderList:
    print "Creating temp dir %s" % (fld);
    os.mkdir(fld);
  
  for fil in fileList:
    print fil
    src_file = os.path.abspath(os.path.join(options['path_to_app_src'], fil))
    dst_file = os.path.abspath(os.path.join(tmp_app_path, fil))
    print "- copying file -"
    print "[SRC] %s " % src_file
    print "[DST] %s " % dst_file
    apply_slimit = options['slimit'] and (os.path.splitext(src_file)[1] == '.js') and (not "node_modules" in src_file)
    
    if not apply_slimit:
        shutil.copy(src_file, dst_file)
    else:
        print "\t Minifying js ... "
        with open(src_file, 'r') as f:
            src_string = f.read()
            dst_string = minify(src_string, mangle=True);
            dst_fp     = open(dst_file, 'wb')
            dst_fp.write(dst_string)
            dst_fp.close()
    
  #for name in os.listdir(top):
  #  if not name in ignore_dirs:
  #    if os.path.isfile(name):
  #      shutil.copy(name, os.path.join(tmp_app_path, name))
  #    else:
  #      shutil.copytree(name, os.path.join(tmp_app_path, name))
  """"""

  app_zip_path = os.path.join(options['path_for_package'], app_name)
  if os.path.isfile(app_zip_path + '.nw'):
    os.remove(app_zip_path + '.nw')


  shutil.make_archive(app_zip_path, 'zip', tmp_app_path)

  print 'Compressing app ends.'

  shutil.rmtree(tmp_app_path)
  shutil.move(app_zip_path + '.zip', app_zip_path + '.nw')
  os.chdir(tmp_cwd)


def GenerateExecutableApp(nw_path, target):
  exec_app_path = options['path_for_exec_app'] + nwfiles.GetPlatformArch(target)
  package_path = options['path_for_package']
  app_tar_name = options['app_name'] + '.nw'
  # make directory
  if os.path.isdir(exec_app_path):
    shutil.rmtree(exec_app_path)
  os.mkdir(exec_app_path)


  print "package app with node-webkit"

  """ copy nw binaries files """
  for file in nwfiles.REQUIRE_FILES_FOR_APP[target]:
    src = os.path.join(nw_path, file)
    dst = os.path.join(exec_app_path, file)
    if os.path.isfile(src):
        shutil.copy(src, dst)
    else:
        shutil.copytree(src, dst)


  if nwfiles.GetPlatformName(target) == nwfiles.PLATFORMNAMEMAC:
    shutil.copy(os.path.join(package_path, app_tar_name),
                os.path.join(exec_app_path,
                             'node-webkit.app',
                             'Contents',
                             'Resources',
                             'app.nw'))
  else:
    shutil.copy(os.path.join(package_path, app_tar_name),
                os.path.join(exec_app_path, app_tar_name))


  tmp_cwd = os.getcwd()
  os.chdir(exec_app_path)
  if is_cygwin or is_linux or is_darwin:
    if nwfiles.GetPlatformName(target) == nwfiles.PLATFORMNAMELINUX:
      sp_args = ['cat', 'nw', app_tar_name, '>', 'app', '&&', 'chmod', '+x', 'app']
      #subprocess.call('cat nw %s > app && chmod +x app' % (app_tar_name), shell=True)
    if nwfiles.GetPlatformName(target) == nwfiles.PLATFORMNAMEWIN:
      sp_args = ['cat', 'nw.exe', app_tar_name, '>', 'app.exe', '&&', 'chmod', '+x', 'app.exe']
      #subprocess.call('cat nw.exe %s > app.exe && chmod +x app.exe' % (app_tar_name), shell=True)
  elif is_win:
    if nwfiles.GetPlatformName(target) == nwfiles.PLATFORMNAMELINUX:
      sp_args = ['copy', '/b', 'nw', '+', app_tar_name, 'app']
      #subprocess.call('copy /b nw+%s app' % (app_tar_name), shell=True)
    if nwfiles.GetPlatformName(target) == nwfiles.PLATFORMNAMEWIN:
      #subprocess.call('copy /b nw.exe+%s app.exe' % (app_tar_name), shell=True)
      sp_args = ['copy', '/b', 'nw.exe', '+', app_tar_name, 'app.exe']

    subprocess.call(sp_args, shell=True)

  if nwfiles.GetPlatformName(target) == nwfiles.PLATFORMNAMELINUX:
    os.remove('nw')
  if nwfiles.GetPlatformName(target) == nwfiles.PLATFORMNAMEWIN:
    os.remove('nw.exe')

  if os.path.isfile(app_tar_name):
    os.remove(app_tar_name)

  os.chdir(tmp_cwd)

def CheckNwFiles(target):
  """
    --nw-path and --nw-ver, most one can be set.
    if --nw-path is set, use this nw'binary and don't download from web.
    if --nw-ver, download this version's node-webkit.
    if both not, download the latest node-webkit.
  """
  _is_download_ = False
  if not options.has_key('path_to_nw'):
    _is_download_ = True
  else:
    nw_path = options['path_to_nw']

  nw_ver = ''
  if options.has_key('nw_version'):
    nw_ver = options['nw_version']

  # download file
  if nw_ver != '':
    print 'Download node-webkit binary'
    nw_path = getnwfromnet.GetNwFromNet(nw_ver, target, options['keep'])
    if not nw_path:
      print 'Failed at downloading'
      return None
  print "checking %s %s" % (nw_path, target)
  if not nwfiles.CheckNwFiles(nw_path, target):
    print 'files are not completed.'
    return None

  return nw_path


def PackageApp(targets):
  # make directory
  if not os.path.isdir(options['path_for_package']):
    os.mkdir(options['path_for_package'])
  MakeZip()

  """ get node-webkit version """
  if not options.has_key('path_to_nw') and not options.has_key('nw_version'):
    print 'Get newest stable version'
    options['nw_version'] = getlatestversion.latestVersion()

  for t in targets:
    nw_path = CheckNwFiles(t)
    if not nw_path:
      continue
    GenerateExecutableApp(nw_path, t)


def __add_argument(parser):
  parser.add_argument("app_path",
                      help="path to the application that been packaged")

  g = parser.add_argument_group('exclusive options',
                                'As for following options, at most one can be set')
  group = g.add_mutually_exclusive_group()
  group.add_argument("--nw-path",
                      help="path to nw binary files that to be packaged with")
  group.add_argument("--nw-ver",
                      help="the stable version of node-webkit to be download")
  parser.add_argument("--keep",
                      action='store_true',
                      help="keep download files")
  parser.add_argument("--slimit", action="store_true", help="Compress javascript using slimit package")



def main(app_path, nw_path, nw_ver, **kw):

  targets = set()

  """ generate target list """
  nwfiles.GetTargetList(targets, kw)

  global options
  options = {
    'path_to_app_src': '',
    'path_for_package': "",
    'path_for_exec_app': '',
    'app_name': '',
    'keep': kw['keep'],
    'slimit': kw['slimit']
  }
  
  if (options['slimit']):
    try:
        from slimit import minify
    except ImportError:
        print "*** FATAL ERROR: "
        print "--slimit option was specified but the module can not be imported. Install it or remove the --slimit option"
        sys.exit(1);
  
  options['path_to_app_src'] = os.path.abspath(app_path)
  options['path_for_package'] = os.path.join(options['path_to_app_src'], _DIR_FOR_APP)
  options['path_for_exec_app'] = os.path.join(options['path_for_package'], _DIR_FOR_EXEC)
  options['app_name'] = os.path.basename(options['path_to_app_src'])

  path_to_app = options['path_to_app_src']

  if not os.path.isdir(path_to_app):
    print 'no such directory: %s' % (path_to_app)
    return

  if nw_path:
    options['path_to_nw'] = nw_path
  if nw_ver:
    options['nw_version'] = nw_ver
    if not CheckVer(nw_ver):
      return

  PackageApp(targets)
