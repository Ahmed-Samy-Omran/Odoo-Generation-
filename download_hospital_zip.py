import urllib.request
url = 'https://qnkidasiemptwakjzwev.supabase.co/storage/v1/object/public/modules/hospital_management.zip?'
outfile = 'hospital_management.zip'
urllib.request.urlretrieve(url, outfile)
print(f'Downloaded {outfile}')
