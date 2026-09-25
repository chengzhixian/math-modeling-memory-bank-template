"""CHM-owned consumer for CYJ's immutable v4 release (no upstream files overwritten)."""
from contextlib import contextmanager
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ROOT=Path(__file__).resolve().parents[2]
RELEASE='3471530d91c8ee7eb709e5cd6c824eb9c423e0df'
MANIFEST='outputs/cyj/interfaces/chm_v4_manifest.json'
MANIFEST_SHA='dcd50430b88cc754e1d8f43a3890013bcc45b07f877b315e9a812d2978fd41f7'


def blob(path,ref=RELEASE):
    return subprocess.check_output(['git','show',f'{ref}:{path}'],cwd=ROOT)


@contextmanager
def consume_release():
    raw=blob(MANIFEST)
    if hashlib.sha256(raw).hexdigest()!=MANIFEST_SHA:raise ValueError('release manifest mismatch')
    manifest=json.loads(raw)
    # Snapshot lives below the consumer Git root so the producer's pinned Q1
    # git-object loader works. Temporary upstream files are removed on exit.
    archive=subprocess.check_output(['git','archive',RELEASE,'src/cyj','outputs/cyj'],cwd=ROOT)
    with tempfile.TemporaryDirectory(prefix='.cyj-v4-',dir=ROOT) as directory:
        snapshot=Path(directory)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(snapshot,filter='data')
        for path,digest in manifest['files_sha256_utf8_lf'].items():
            data=(snapshot/path).read_bytes().replace(b'\r\n',b'\n')
            if hashlib.sha256(data).hexdigest()!=digest:raise ValueError(f'hash mismatch: {path}')
        sys.path.insert(0,str(snapshot/'src/cyj'))
        try:
            from chm_adapter_v4 import CHMAdapterV4
            from chm_consumer_smoke_v4 import check
            smoke=check(RELEASE)
            model=CHMAdapterV4(mode='conditional_diagnostic')
            yield model,manifest,smoke
        finally:
            sys.path.remove(str(snapshot/'src/cyj'))
            for name,module in list(sys.modules.items()):
                if str(getattr(module,'__file__','')).startswith(str(snapshot)):
                    del sys.modules[name]


class SolverAdapter:
    def __init__(self,producer):
        from q3_generic_solver import Support
        self.producer=producer
        self.support=Support(*producer.bounds)

    def value_grad(self,n,d,q):
        # exp(log(bound)) may miss the strict producer boundary by a few ulps.
        values=[]
        for x,(lo,hi) in zip((n,d,q),self.producer.bounds):
            if x<lo and lo-x<=8*max(abs(lo),1)*sys.float_info.epsilon:x=lo
            if x>hi and x-hi<=8*max(abs(hi),1)*sys.float_info.epsilon:x=hi
            values.append(x)
        return self.producer.value_grad(*values)
