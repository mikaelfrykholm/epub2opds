#!/usr/bin/env python3
#  © Mikael Frykholm <mikael@frykholm.com>
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import zipfile
from xml.etree import ElementTree 
import genshi.template
import os

def get_epub_info(fname):
    ns = {
        'n':'urn:oasis:names:tc:opendocument:xmlns:container',
        'pkg':'http://www.idpf.org/2007/opf',
        'dc':'http://purl.org/dc/elements/1.1/'
    }
    
    # prepare to read from the .epub file
    zip = zipfile.ZipFile(fname)

    # find the contents metafile
    txt = zip.read('META-INF/container.xml')
    tree = ElementTree.fromstring(txt)
    cfname = tree.find('n:rootfiles/n:rootfile',namespaces=ns).attrib['full-path']

    # grab the metadata block from the contents metafile
    cf = zip.read(cfname)
    tree = ElementTree.fromstring(cf)
    p = tree.find('pkg:metadata',namespaces=ns)
    manifest = tree.find('pkg:manifest',namespaces=ns)
    coverid = p.findall('pkg:meta/[@name="cover"]',namespaces=ns)[0].attrib['content']
    coverpath = manifest.find('pkg:item[@id="%s"]'%coverid, namespaces=ns).attrib['href']    
    try:
       cover=zip.read(coverpath)
    except(KeyError):
        cover=None

    # repackage the data
    res = {}
    res['filename'] = fname
    res['cover'] = cover
#    import pdb;pdb.set_trace()
    
    for name in ['title','language','creator','date','identifier','description']:
        if p.find('dc:'+name, namespaces=ns) is not None:
            res[name] = p.find('dc:'+name, namespaces=ns).text
        else:
            res[name] = None
    if p.find('dc:identifier[@pkg:scheme="uuid"]', namespaces=ns) is not None:
        res['uuid'] = p.find('dc:identifier[@pkg:scheme="uuid"]', namespaces=ns).text
    else:
        res['uuid'] = None
    return res

def generate_opds(books, output_dir):
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        f = open('opds.atom', 'w')
        loader = genshi.template.TemplateLoader([os.curdir])
        tmpl = loader.load('opds.xml')
        tmpl_vars = {'books': books}                     
        for book in books:
            cpath = os.path.join(output_dir, '%s.jpg'%book['identifier'])
            book['coverpath'] = "%s.jpg"%book['identifier']
            if not os.path.exists(cpath) and book['cover']:
                cover = open(cpath,'wb')
                cover.write(book['cover'])
                cover.close()
        return f.write(tmpl.generate(**tmpl_vars).render())

def find_epubs(dir):
    for (root, dirs, files) in os.walk(dir):
        for file in files:
            if file.lower().endswith('.epub'):
                yield(os.path.join(root,file))
            

if __name__ == "__main__":
    import sys
    books = []
    for path in find_epubs(sys.argv[1]):
        books.append(get_epub_info(path))
    generate_opds(books, '.covers')
    print("Generated feed for %d books."%len(books))
