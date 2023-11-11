import unittest
from forwarding_table import ForwardingTable
from table_entry import TableEntry


class TestForwardingTable(unittest.TestCase):

    def test_forwarding_table_insertion(self):
        table = ForwardingTable()
        destination = '192.168.56.100'
        next_hops = ['192.168.56.101', '192.168.56.102']
        delay = 10
        loss = 0.2
        table.add_entry(destination, next_hops, delay, loss)
        consult = table.consult_entry(destination)
        te = TableEntry(next_hops, delay, loss)
        self.assertEqual(consult.delay, te.delay)
        self.assertEqual(consult.loss, te.loss)
        self.assertEqual(consult.next_hops, te.next_hops)

    def test_forwarding_table_removal(self):
        table = ForwardingTable()
        destination = '192.168.56.100'
        next_hops = ['192.168.56.101', '192.168.56.102']
        delay = 10
        loss = 0.2
        table.add_entry(destination, next_hops, delay, loss)
        table.remove_entry(destination)
        self.assertEqual(table.table, {})




