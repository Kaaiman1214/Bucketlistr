import re

from .utils import fold

FLAG_BASE_URL = 'https://hatscripts.github.io/circle-flags/flags/'

_PLACES = """
ad|Andorra
ae|United Arab Emirates
af|Afghanistan
ag|Antigua and Barbuda
ai|Anguilla
al|Albania
am|Armenia
ao|Angola
aq|Antarctica
ar|Argentina
as|American Samoa
at|Austria
au|Australia
au-act|Australian Capital Territory
au-nsw|New South Wales
au-nt|Northern Territory
au-qld|Queensland
au-sa|South Australia
au-tas|Tasmania
au-vic|Victoria
au-wa|Western Australia
aw|Aruba
ax|Åland Islands
az|Azerbaijan
ba|Bosnia and Herzegovina
bb|Barbados
bd|Bangladesh
be|Belgium
bf|Burkina Faso
bg|Bulgaria
bh|Bahrain
bi|Burundi
bj|Benin
bl|Saint Barthélemy
bm|Bermuda
bn|Brunei
bo|Bolivia
bq-bo|Bonaire
bq-sa|Saba
bq-se|Sint Eustatius
br|Brazil
bs|Bahamas
bt|Bhutan
bv|Bouvet Island
bw|Botswana
by|Belarus
bz|Belize
ca|Canada
ca-bc|British Columbia
cc|Cocos (Keeling) Islands
cd|Congo (Democratic Republic)
cf|Central African Republic
cg|Congo (Republic)
ch|Switzerland
ch-gr|Grisons
ci|Ivory Coast
ck|Cook Islands
cl|Chile
cm|Cameroon
cn|China
cn-xj|Xinjiang
co|Colombia
cq|Sark
cr|Costa Rica
cu|Cuba
cv|Cabo Verde
cw|Curaçao
cx|Christmas Island
cy|Cyprus
cz|Czechia
de|Germany
dj|Djibouti
dk|Denmark
dm|Dominica
do|Dominican Republic
dz|Algeria
easter_island|Easter Island
ec|Ecuador
ec-w|Galápagos
ee|Estonia
eg|Egypt
eh|Western Sahara
er|Eritrea
es|Spain
es-ar|Aragon
es-ce|Ceuta
es-cn|Canary Islands
es-ct|Catalonia
es-ga|Galicia
es-ib|Balearic Islands
es-ml|Melilla
es-pv|Basque Country
et|Ethiopia
et-or|Oromia
et-ti|Tigray
fi|Finland
fj|Fiji
fk|Falkland Islands
fm|Micronesia
fo|Faroe Islands
fr|France
fr-20r|Corsica
fr-bre|Brittany
fr-cp|Clipperton Island
ga|Gabon
gb|United Kingdom
gb-con|Cornwall
gb-eng|England
gb-nir|Northern Ireland
gb-ork|Orkney
gb-sct|Scotland
gb-wls|Wales
gd|Grenada
ge|Georgia
ge-ab|Abkhazia
gf|French Guiana
gg|Guernsey
gh|Ghana
gi|Gibraltar
gl|Greenland
gm|Gambia
gn|Guinea
gp|Guadeloupe
gq|Equatorial Guinea
gr|Greece
gs|South Georgia and the South Sandwich Islands
gt|Guatemala
gu|Guam
gw|Guinea-Bissau
gy|Guyana
hk|Hong Kong
hm|Heard Island and McDonald Islands
hn|Honduras
hr|Croatia
ht|Haiti
hu|Hungary
id|Indonesia
id-jb|West Java
id-jt|Central Java
ie|Ireland
il|Israel
im|Isle of Man
in|India
in-as|Assam
in-gj|Gujarat
in-ka|Karnataka
in-mn|Manipur
in-mz|Mizoram
in-or|Odisha
in-tg|Telangana
in-tn|Tamil Nadu
io|British Indian Ocean Territory
iq|Iraq
iq-kr|Kurdistan
ir|Iran
is|Iceland
it|Italy
it-23|Aosta Valley
it-82|Sicily
it-88|Sardinia
je|Jersey
jm|Jamaica
jo|Jordan
jp|Japan
ke|Kenya
kg|Kyrgyzstan
kh|Cambodia
ki|Kiribati
km|Comoros
kn|Saint Kitts and Nevis
kp|North Korea
kr|South Korea
kw|Kuwait
ky|Cayman Islands
kz|Kazakhstan
la|Laos
lb|Lebanon
lc|Saint Lucia
li|Liechtenstein
lk|Sri Lanka
lr|Liberia
ls|Lesotho
lt|Lithuania
lu|Luxembourg
lv|Latvia
ly|Libya
ma|Morocco
mc|Monaco
md|Moldova
me|Montenegro
mf|Saint Martin
mg|Madagascar
mh|Marshall Islands
mk|North Macedonia
ml|Mali
mm|Myanmar
mn|Mongolia
mo|Macau
mp|Northern Mariana Islands
mq|Martinique
mr|Mauritania
ms|Montserrat
mt|Malta
mu|Mauritius
mv|Maldives
mw|Malawi
mx|Mexico
my|Malaysia
mz|Mozambique
na|Namibia
nc|New Caledonia
ne|Niger
nf|Norfolk Island
ng|Nigeria
ni|Nicaragua
nl|Netherlands
nl-fr|Friesland
no|Norway
northern_cyprus|Northern Cyprus
np|Nepal
nr|Nauru
nu|Niue
nz|New Zealand
occitania|Occitania
om|Oman
pa|Panama
pe|Peru
pf|French Polynesia
pg|Papua New Guinea
ph|Philippines
pk|Pakistan
pk-jk|Azad Kashmir
pk-sd|Sindh
pl|Poland
pm|Saint Pierre and Miquelon
pn|Pitcairn Islands
pr|Puerto Rico
ps|Palestine
pt|Portugal
pt-20|Azores
pt-30|Madeira
pw|Palau
py|Paraguay
qa|Qatar
re|Réunion
ro|Romania
rs|Serbia
ru|Russia
ru-ba|Bashkortostan
ru-ce|Chechnya
ru-cu|Chuvashia
ru-da|Dagestan
ru-ko|Komi Republic
ru-ta|Tatarstan
ru-ud|Udmurtia
rw|Rwanda
sa|Saudi Arabia
sb|Solomon Islands
sc|Seychelles
sd|Sudan
se|Sweden
sg|Singapore
sh-ac|Ascension Island
sh-hl|Saint Helena
sh-ta|Tristan da Cunha
si|Slovenia
sj|Svalbard and Jan Mayen
sk|Slovakia
sl|Sierra Leone
sm|San Marino
sn|Senegal
so|Somalia
somaliland|Somaliland
south_ossetia|South Ossetia
sr|Suriname
ss|South Sudan
st|São Tomé and Príncipe
sv|El Salvador
sx|Sint Maarten
sy|Syria
sz|Eswatini
tc|Turks and Caicos Islands
td|Chad
tf|French Southern Territories
tg|Togo
th|Thailand
tibet|Tibet
tj|Tajikistan
tk|Tokelau
tl|Timor-Leste
tm|Turkmenistan
tn|Tunisia
to|Tonga
torres_strait_islands|Torres Strait Islands
tr|Turkey
transnistria|Transnistria
tt|Trinidad and Tobago
tv|Tuvalu
tw|Taiwan
tz|Tanzania
ua|Ukraine
ug|Uganda
um|United States Minor Outlying Islands
us|United States
us-ak|Alaska
us-al|Alabama
us-ar|Arkansas
us-az|Arizona
us-ca|California
us-co|Colorado
us-dc|Washington, D.C.
us-fl|Florida
us-ga|Georgia (U.S. state)
us-hi|Hawaii
us-in|Indiana
us-mo|Missouri
us-ms|Mississippi
us-nc|North Carolina
us-nm|New Mexico
us-ri|Rhode Island
us-tn|Tennessee
us-tx|Texas
uy|Uruguay
uz|Uzbekistan
va|Vatican City
vc|Saint Vincent and the Grenadines
ve|Venezuela
vg|British Virgin Islands
vi|U.S. Virgin Islands
vn|Vietnam
vu|Vanuatu
wf|Wallis and Futuna
ws|Samoa
xk|Kosovo
ye|Yemen
yt|Mayotte
za|South Africa
zm|Zambia
zw|Zimbabwe
"""

COUNTRIES = {}
for _line in _PLACES.strip().splitlines():
    _code, _name = _line.split('|', 1)
    COUNTRIES[_code] = _name


def flag_url(code):
    if code in COUNTRIES:
        return f'{FLAG_BASE_URL}{code}.svg'
    return None


def _is_country(code):
    return re.fullmatch(r'[a-z]{2}', code) is not None and code != 'cq'


def _by_name(codes):
    return sorted(((code, COUNTRIES[code]) for code in codes),
                  key=lambda pair: fold(pair[1]))


COUNTRY_GROUPS = [
    ('Countries and territories',
     _by_name(code for code in COUNTRIES if _is_country(code))),
    ('Regions and other places',
     _by_name(code for code in COUNTRIES if not _is_country(code))),
]
