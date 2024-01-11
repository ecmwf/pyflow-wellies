from wellies import mars

req = dict(
    DOMAIN="G",
    EXPVER=1,
    CLASS="ce",
    TYPE="SFO",
    STREAM="wfcl",
    DATE=20221001,
    ORIGIN="ECMF",
    LEVTYPE="SFC",
    STEP=24,
    MODEL="GLOBAL_LISFLOOD",
    PARAM=240024,
    DATABASE="marsscratch",
    HDATE=20221209,
    TIME=[0, 6, 12, 18],
)


def test_request():
    req = [
        (
            "retrieve",
            dict(
                type="analysis",
                time=12,
                date=-1,
                grid=2.5 / 2.5,
                param="u",
                fieldset="u",
            ),
        ),
        ("retrieve", dict(param="v", fieldset="v")),
        ("compute", dict(formula="sqrt(u*u + v*v)", target="speed")),
    ]
    request = str(mars.Request(req, command="fdb"))
    request_check = """
fdb << EOF
retrieve,
  type=analysis,
  time=12,
  date=-1,
  grid=1.0,
  param=u,
  fieldset=u
retrieve,
  param=v,
  fieldset=v
compute,
  formula="sqrt(u*u + v*v)",
  target="speed"
EOF
"""
    print(request)
    print(request_check)
    assert request == request_check


def test_archive():
    request = str(mars.Archive(req, source="dis.grb"))
    request_check = """
mars << EOF
archive,
  DOMAIN=G,
  EXPVER=1,
  CLASS=ce,
  TYPE=SFO,
  STREAM=wfcl,
  DATE=20221001,
  ORIGIN=ECMF,
  LEVTYPE=SFC,
  STEP=24,
  MODEL=GLOBAL_LISFLOOD,
  PARAM=240024,
  DATABASE=marsscratch,
  HDATE=20221209,
  TIME=0/6/12/18,
  source="dis.grb"
EOF
"""
    print(request)
    print(request_check)
    assert request == request_check


def test_list():
    request = str(mars.List(req))
    request_check = """
mars << EOF
list,
  DOMAIN=G,
  EXPVER=1,
  CLASS=ce,
  TYPE=SFO,
  STREAM=wfcl,
  DATE=20221001,
  ORIGIN=ECMF,
  LEVTYPE=SFC,
  STEP=24,
  MODEL=GLOBAL_LISFLOOD,
  PARAM=240024,
  DATABASE=marsscratch,
  HDATE=20221209,
  TIME=0/6/12/18
EOF
"""
    print(request)
    print(request_check)
    assert request == request_check


def test_retrieve():
    request = str(mars.Retrieve(req, target="dis.grb"))
    request_check = """
mars << EOF
retrieve,
  DOMAIN=G,
  EXPVER=1,
  CLASS=ce,
  TYPE=SFO,
  STREAM=wfcl,
  DATE=20221001,
  ORIGIN=ECMF,
  LEVTYPE=SFC,
  STEP=24,
  MODEL=GLOBAL_LISFLOOD,
  PARAM=240024,
  DATABASE=marsscratch,
  HDATE=20221209,
  TIME=0/6/12/18,
  target="dis.grb"
EOF
"""
    assert request == request_check

    request = str(mars.Retrieve(req, target="dis.grb", command="fdb"))
    request_check = """
fdb << EOF
retrieve,
  DOMAIN=G,
  EXPVER=1,
  CLASS=ce,
  TYPE=SFO,
  STREAM=wfcl,
  DATE=20221001,
  ORIGIN=ECMF,
  LEVTYPE=SFC,
  STEP=24,
  MODEL=GLOBAL_LISFLOOD,
  PARAM=240024,
  DATABASE=marsscratch,
  HDATE=20221209,
  TIME=0/6/12/18,
  target="dis.grb"
EOF
"""
    print(request)
    print(request_check)
    assert request == request_check
